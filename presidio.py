import io
from presidio_analyzer import AnalyzerEngine, RecognizerResult
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_analyzer.recognizer_registry import RecognizerRegistryProvider

from src.hooks.config import DEFAULT_LANGUAGE_CODE
from src.hooks.presidio.scanner import PresidioScanner


def run_line_test():
    # import spacy

    # nlp = spacy.load("en_core_web_lg")
    # doc = nlp("Format Python code using ruff format via just command")

    # for ent in doc.ents:
    #     print(ent.text, ent.start_char, ent.end_char, ent.label_)
    # return
    print("Scan line by line")
    file_path = "tests/test_data/personal_data.yaml"
    analyzer = PresidioScanner()._get_analyzer()
    entities = analyzer.get_supported_entities()
    with io.open(file_path, "r", encoding="utf-8") as file_contents:
        for line_number, line in enumerate(file_contents):
            results = analyzer.analyze(
                text=line,
                language=DEFAULT_LANGUAGE_CODE,
                entities=entities,
                return_decision_process=True,
                # score_threshold=1.0,
            )
            for result in results:
                print(f" {result}, text: {line[result.start : result.end]}")
                # print("line number: ", line_number + 1)
                # print(result, result.analysis_explanation, result.recognition_metadata, result)


def run_file_contents_test():
    print("Scan entire file")
    file_path = "tests/test_data/personal_data.yaml"
    analyzer = PresidioScanner()._get_analyzer()
    entities = analyzer.get_supported_entities()
    with io.open(file_path, "r", encoding="utf-8") as file_contents:
        text = file_contents.read()
        results = analyzer.analyze(
            text=text,
            language=DEFAULT_LANGUAGE_CODE,
            entities=entities,
            return_decision_process=True,
            # score_threshold=1.0,
        )
        for result in results:
            print(f" {result}, text: {text[result.start : result.end]}")
            # print(result, result.analysis_explanation, result.recognition_metadata, result)


run_line_test()
run_file_contents_test()
