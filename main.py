import os

import numpy as np

import data_struc
from config import Config
import logging
from utils import *
import time
from numpy import interp
from aeon.datasets import load_from_tsv_file, write_to_tsfile, load_from_tsfile

import argparse

# Configure logging to write to a file
parser = argparse.ArgumentParser(description="Process some integers.")
parser.add_argument("--debug", type=str, help="if debug mode", default=True)

args = parser.parse_args()
config = Config()

data_path = config.data_debug_path if args.debug == True else config.data_path

if __name__ == "__main__":
    np.random.seed(config.seed)
    # Configure logging to write to a file
    logging.basicConfig(filename=config.log_path, level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')

    datasets_list = os.listdir(data_path)
    datasets_list = [x for x in datasets_list if not x.endswith('.csv') and not x.startswith('.')]

    for data_name in datasets_list:
        logging.info(f"Processing {data_name}")

        data, target, meta_data = load_from_tsfile(os.path.join(data_path, data_name, f"{data_name}.ts"),
                                                   return_meta_data=True)
        target = target.astype(int)
        # Plot the mean ROC curve
        plt.figure(figsize=(10, 6))

        for oversampler_name in config.oversampling_methods:
            start_time = time.time()
            logging.info(f"Using {oversampler_name} over-sampling method")
            logging.info("-" * 50)

            seeds = np.random.randint(0, 10000, 10)

            # Initialize lists to store metrics
            accuracy_scores = []
            precision_scores = []
            recall_scores = []
            f1_scores = []
            roc_auc_scores = []
            all_fpr = []
            all_tpr = []
            mean_fpr = np.linspace(0, 1, 100)

            for fold, seed in enumerate(seeds):
                X_train, X_test, y_train, y_test = data_struc.split_data(data, target, data_name, seed,
                                                                         data_path=data_path)

                X_train_imb, y_train_imb, minority_num = data_struc.make_imbalance(
                    X_train, y_train, sampling_ratio=config.imbalance_ratio, minority_num=True)

                logging.info(f'Fold {fold + 1}')
                logging.info(f"Training set distribution: {np.unique(y_train_imb, return_counts=True)}")
                logging.info(f"Test set distribution: {np.unique(y_test, return_counts=True)}\n")
                logging.info(f"Minority class number: {minority_num}")
                if minority_num <= 6:
                    logging.info(f"Minority class number less than 6, skipping this fold")
                    continue

                oversampler = getattr(OverSamplingMethods(), oversampler_name)()
                X_sampled, y_sampled = oversampler.fit_resample(np.squeeze(X_train_imb), y_train_imb)
                X_sampled = np.expand_dims(X_sampled, axis=1)
                clf = getattr(ClassificationMetrics(), config.classifier)()
                clf.fit(X_sampled, y_sampled)
                y_pred = clf.predict(X_test)
                y_pred_proba = clf.predict_proba(X_test)
                accuracy, precision, recall, f1, roc_auc_value, fpr, tpr \
                    = metric_factors(y_test, y_pred, y_pred_proba, verbose=False)

                accuracy_scores.append(accuracy)
                precision_scores.append(precision)
                recall_scores.append(recall)
                f1_scores.append(f1)
                roc_auc_scores.append(roc_auc_value)

                all_fpr.append(fpr)
                all_tpr.append(tpr)

            if len(all_fpr) == 0:
                logging.info(f"Skipping {oversampler_name} over-sampling method")
                continue
            # Calculate average metrics
            avg_accuracy = np.mean(accuracy_scores)
            avg_precision = np.mean(precision_scores)
            avg_recall = np.mean(recall_scores)
            avg_f1 = np.mean(f1_scores)
            avg_roc_auc = np.mean(roc_auc_scores)

            # calculate mean ROC curve
            mean_tpr_all = []
            for i in range(len(all_fpr)):
                mean_tpr_all.append(interp(mean_fpr, all_fpr[i], all_tpr[i]))
            mean_tpr_all = np.array(mean_tpr_all)
            mean_tpr = np.mean(mean_tpr_all, axis=0)

            # ensure the ROC curve  ends at 1 ,1
            mean_tpr[-1] = 1.0
            plt.plot(mean_fpr, mean_tpr, label=f'{oversampler_name} ROC curve (AUC = {avg_roc_auc:.2f})')
            # verbose
            end_time = time.time()
            logging.info(f'Average Accuracy: {avg_accuracy:.4f}')
            logging.info(f'Average Precision: {avg_precision:.4f}')
            logging.info(f'Average Recall: {avg_recall:.4f}')
            logging.info(f'Average F1 Score: {avg_f1:.4f}')
            logging.info(f'Average ROC AUC: {avg_roc_auc:.4f}')
            logging.info(f'Time taken: {end_time - start_time:.2f} seconds')
            logging.info("*" * 50)

        plt.plot([0, 1], [0, 1], color='red', linestyle='--')  # Random classifier line
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.0])
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title(f'Mean Receiver Operating Characteristic (ROC) Curve in {data_name}')
        plt.legend(loc='lower right')
        plt.grid()
        plt.savefig(f'./img/{data_name}_roc_curve.png', dpi=300)
        plt.show()
