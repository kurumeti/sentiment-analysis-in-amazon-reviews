import pipelines
import argparse

from colorama import init as init_colorama
from colorama import Fore

from timeit import default_timer as timer

from definitions import TRAIN_PATH

from data.preprocessor import Options
from data.loaders import load_and_clean_data

from sklearn import metrics
from sklearn.model_selection import train_test_split
from sklearn.svm import LinearSVC
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.ensemble import GradientBoostingClassifier


ROWS = 50000

init_colorama()


def color_text(text, color):
    return color + text + Fore.RESET


def embedding_pipelines():
    yield ("Doc2Vec", pipelines.doc2vec())
    yield ("Word2Vec", pipelines.word2vec_mean_embedding())
    yield ("Word2Vec + TFIDF", pipelines.word2vec_mean_embedding(tf_idf=True))
    yield ("GloVe", pipelines.glove_mean_embedding())
    yield ("GloVe + TFIDF", pipelines.glove_mean_embedding(tf_idf=True))


def gradient_boosting_pipeline():
    gradent_boosting = pipelines.bag_of_words(
        classifier=GradientBoostingClassifier(
            n_estimators=5000,
            learning_rate=0.2,
            random_state=10
        )
    )

    gradent_boosting_tfidf = pipelines.bag_of_words(
        classifier=GradientBoostingClassifier(
            n_estimators=5000,
            learning_rate=0.2,
            random_state=10
        ),
        tf_idf=True
    )

    gb_pipelines = [
        ("BoN + GB", gradent_boosting),
        ("BoN + GB + TFIDF", gradent_boosting_tfidf)
    ]

    for name, pipe in gb_pipelines:
        pipe.set_params(
            vect__ngram_range=(1, 5),
            vect__max_features=500000,
        )

        yield (name, pipe)


def bag_of_words_pipeline():
    log_regression = pipelines.bag_of_words(
        classifier=LogisticRegression(C=10.0)
    )

    log_regression_tfidf = pipelines.bag_of_words(
        classifier=LogisticRegression(C=10.0),
        tf_idf=True
    )

    bow_pipelines = [
        ("BoW + LR", log_regression),
        ("BoW + LR + TFIDF", log_regression_tfidf)
    ]

    for name, pipe in bow_pipelines:
        pipe.set_params(vect__max_features=50000)

        yield (name, pipe)


def bag_of_ngrams_pipelines():
    log_regression = pipelines.bag_of_words(
        classifier=LogisticRegression(C=10.0),
    )

    log_regression_tfidf = pipelines.bag_of_words(
        classifier=LogisticRegression(C=10.0),
        tf_idf=True
    )

    linear_svc = pipelines.bag_of_words(
        classifier=LinearSVC(),
    )

    linear_svc_tfidf = pipelines.bag_of_words(
        classifier=LinearSVC(),
        tf_idf=True
    )

    multinomial_nb = pipelines.bag_of_words(
        classifier=MultinomialNB(),
    )

    multinomial_nb_tfidf = pipelines.bag_of_words(
        classifier=MultinomialNB(),
        tf_idf=True
    )

    bon_pipelines = [
        ("BoN + LR", log_regression),
        ("BoN + LR + TFIDF", log_regression_tfidf),
        ("BoN + SVC", linear_svc),
        ("BoN + SVC + TFIDF", linear_svc_tfidf),
        ("BoN + MNB", multinomial_nb),
        ("BoN + MNB + TFIDF", multinomial_nb_tfidf),
    ]

    for name, pipe in bon_pipelines:
        pipe.set_params(
            vect__ngram_range=(1, 5),
            vect__max_features=500000
        )

        yield (name, pipe)


def evaluate_pipeline(pipeline, X_train, y_train, X_test, y_test):
    print("-- Training model")
    start = timer()

    pipeline.fit(X_train, y_train)

    training_time = timer() - start

    print("-- Validating model")
    predictions = pipeline.predict(X_test)

    report = metrics.classification_report(
        y_test,
        predictions,
        target_names=["Negative", "Positive"],
        digits=3
    )

    print("\n{}".format(report))

    accuracy = metrics.accuracy_score(y_test, predictions)
    precision = metrics.precision_score(y_test, predictions)
    recall = metrics.recall_score(y_test, predictions)
    f1_score = metrics.f1_score(y_test, predictions)

    return accuracy, precision, recall, f1_score, training_time


def main(model_pipelines):
    options = (
        Options.EMAILS,
        Options.EMOTICONS,
        Options.LEMMATIZER,
        Options.PUNCTUATION,
        Options.REPEATING_VOWELS,
        Options.STOPWORDS,
        Options.URLS
    )

    samples, labels = load_and_clean_data(TRAIN_PATH, options, ROWS)

    X_train, X_test, y_train, y_test = train_test_split(
        samples, labels, test_size=0.25, random_state=42
    )

    for name, model in model_pipelines:
        print("\n\n\t\t\t" + color_text(name, color=Fore.GREEN))
        print("\t\t\t" + "-" * len(name) + "\n")

        accuracy, precision, recall, f1_score, train_time = evaluate_pipeline(
            model,
            X_train, y_train,
            X_test, y_test
        )

        print("Training time: {:.2f}s\n".format(train_time))

        print(color_text("Accuracy:  ", color=Fore.GREEN) +
              color_text("{:.3f}".format(accuracy), color=Fore.RED))

        print(color_text("Precision: ", color=Fore.GREEN) +
              color_text("{:.3f}".format(precision), color=Fore.RED))

        print(color_text("Recall:    ", color=Fore.GREEN) +
              color_text("{:.3f}".format(recall), color=Fore.RED))

        print(color_text("F1-score:  ", color=Fore.GREEN) +
              color_text("{:.3f}".format(f1_score), color=Fore.RED))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Train and evaluate sentiment classification models."
    )

    parser.add_argument("--model", type=str, default="bow")
    args = parser.parse_args()

    if args.model == "bow":
        model_pipelines = bag_of_words_pipeline()
    elif args.model == "bon":
        model_pipelines = bag_of_ngrams_pipelines()
    elif args.model == "gb":
        model_pipelines = gradient_boosting_pipeline()
    elif args.model == "embedding":
        model_pipelines = embedding_pipelines()
    else:
        raise Exception("Invalid classification model type")

    main(model_pipelines)
