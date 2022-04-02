from __future__ import annotations

import string
from collections import Counter, defaultdict
from functools import cached_property
from typing import Dict, Optional, List

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
import spacy
from spacy import Language
from spacy.lang.char_classes import LIST_ELLIPSES, LIST_ICONS, ALPHA_LOWER, ALPHA_UPPER, CONCAT_QUOTES, ALPHA
from spacy.tokens import Token
from spacy.util import compile_infix_regex
from tqdm import tqdm

from app.services.statistics.statistics_calculation import StatisticsCalculation


class StaticStatisticsCalculation(StatisticsCalculation):
    """A class for providing text related statistics using the statically processed data in data lake."""

    @cached_property
    def analyzer(self: StaticStatisticsCalculation) -> Language:
        """The analyzer for text tokenization."""
        analyzer = spacy.load("en_core_web_sm", disable=["parser", "ner"])
        infixes = (
            LIST_ELLIPSES
            + LIST_ICONS
            + [
                r"(?<=[0-9])[+\-\*^](?=[0-9-])",
                r"(?<=[{al}{q}])\.(?=[{au}{q}])".format(al=ALPHA_LOWER, au=ALPHA_UPPER, q=CONCAT_QUOTES),
                r"(?<=[{a}]),(?=[{a}])".format(a=ALPHA),
                # Skip regex that splits on hyphens between letters:
                # r"(?<=[{a}])(?:{h})(?=[{a}])".format(a=ALPHA, h=HYPHENS),
                r"(?<=[{a}0-9])[:<>=/](?=[{a}])".format(a=ALPHA),
            ]
        )
        infix_regex = compile_infix_regex(infixes)
        analyzer.tokenizer.infix_finditer = infix_regex.finditer

        return analyzer

    def calculate_term_tf_idfs(self: StaticStatisticsCalculation, content: str) -> pd.DataFrame:
        term_tfs_dict = self.calculate_term_tfs(content)
        term_tfs = pd.DataFrame(index=term_tfs_dict.keys(), data=term_tfs_dict.values(), columns=["tf"])

        term_dfs = self.article_repository.get_static_term_statistics()

        # The DF (document frequency) for the terms which doesn't exist in any articles is zero.
        term_statistics = term_tfs.join(term_dfs, how="left").fillna(0)

        total_article_counts = self.article_repository.get_static_article_count()
        term_statistics["tf-idf"] = round(
            term_statistics["tf"] * self.calculate_term_idfs(total_article_counts, term_statistics["df"]), 1
        )

        return term_statistics[["tf-idf"]]

    def calculate_term_tfs(self: StaticStatisticsCalculation, content: str) -> Dict[str, int]:
        """Calculate TF (term frequency) for each term in the given text content.

        Args:
            content (str): The text content whose terms should be analyzed.

        Returns:
            Dict[str, int]: A collection of terms as keys and TFs as values.
        """
        return Counter(self.tokenize(content))

    def calculate_all_term_dfs(self: StaticStatisticsCalculation) -> Dict[str, int]:
        """Calculate the DF (document frequency) for all the available term in corpus.

        Returns:
            Dict[str, int]: A collection of terms as keys and DFs as their values.
        """
        article_count = self.article_repository.get_static_article_count()
        progress_bar = tqdm(total=article_count)
        progress_bar.set_description(f"Calculating document frequency for each term in {article_count} articles:")

        term_dfs: Dict[str, int] = defaultdict(int)
        articles = self.article_repository.get_static_articles()["content"]
        for document_content in articles:
            for term in set(self.tokenize(document_content)):
                term_dfs[term] += 1
            progress_bar.update(n=1)

        return term_dfs

    def calculate_all_term_idfs(self: StaticStatisticsCalculation) -> pd.DataFrame:
        """Calculate the IDF (inverse document frequency) for all the available term in corpus.
        @deprecated:
            Instead of calculating and storing the IDFs, it's better to calculate and store the document frequency by
            `calculate_all_term_dfs` method which is more memory efficient and calculate IDF in the request time.
            Comparing to DFs, storing IDFs doesn't make the TF-IDF calculation in the request time any faster,
            because we need to calculate the n (number of documents) parameter in the IDF equation for unavailable terms anyway.

        Returns:
            pd.DataFrame
        """

        vectorizer = TfidfVectorizer(use_idf=True, smooth_idf=True, tokenizer=self.tokenize)
        vectorizer.fit_transform(self.article_repository.get_static_articles()["content"])

        term_idfs = pd.DataFrame({"term": vectorizer.get_feature_names_out(), "idf": vectorizer.idf_})
        term_idfs["idf"] = term_idfs["idf"].round(self.IDF_DECIMAL_PLACE_COUNT)

        return term_idfs

    def tokenize(self: StaticStatisticsCalculation, text: str) -> List[str]:
        """Tokenize the given text into terms by the class analyzer.

        Args:
            text (str):

        Returns:
            List[str]: A collection of terms.
        """
        return [term for token in self.analyzer(text) if (term := self.convert_token_to_term(token))]

    def convert_token_to_term(self: StaticStatisticsCalculation, token: Token) -> Optional[str]:
        """Convert the given token to a term in our desired format if possible.

        Args:
            token (Token):

        Returns:
            (str, optional): A textual term in our desired format.
        """
        if token.is_stop:
            return None

        # The desired term format is the word lemma in lower case.
        term = token.lemma_.lower()

        # Clean the term by removing noisy characters (e.g. digits, punctuations, whitespaces).
        # - and . are only allowed as infix characters.
        noise_character_pattern = string.digits + string.whitespace + r"""!"#$%&'()*+,/:;<=>?@[\]^_`{|}~"""
        noise_suffix_prefix_pattern = r"-."
        term = term.translate(str.maketrans("", "", noise_character_pattern)).strip(noise_suffix_prefix_pattern)

        # Terms should have more than one character.
        return term if len(term) > 1 else None
