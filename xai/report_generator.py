from xai.report import TrainingReportFPDF
from xai.data_explorer.data_analysis import prepare_data_metafile
from xai.evaluation.binary_classification_result import BinaryClassificationResult
from xai.evaluation.multi_classification_result import MultiClassificationResult
from xai.report_params import Params
from xai.graphs.generate_combo_figures import visualize_feature_for_similar_classes
from xai.util import JsonSerializable
import xai.recommendations.recommendation as rec
import xai.graphs.graph_generator as gg
import xai.graphs.format_contants as graph_constants
from xai import constants
from xai import util
import numpy as np

import json
import os
import logging
import datetime
import shutil

LOGGER = logging.getLogger(__name__)


class ReportGenerator(TrainingReportFPDF):
    def __init__(self, report_params, report_data):
        super(ReportGenerator, self).__init__()
        self.report_params = report_params
        self.report_data = report_data
        self.setup_report_info()
        if not os.path.exists(constants.FIGURE_PATH):
            os.mkdir(constants.FIGURE_PATH)

    def generate_report(self, output_path):
        chapter_links = self.generate_cover_page(self.report_params.content_list, self.report_data)
        for (content_page, chapter_link) in zip(self.report_params.content_list, chapter_links):
            self.add_chapter(content_page, link=chapter_link)
        self.output_report(output_path)

    def add_chapter(self, chapter_content, link=None):
        if chapter_content == constants.CONTENT_DATA:
            self.generate_data_analysis(link)
        elif chapter_content == constants.CONTENT_FEATURE:
            self.generate_feature_analysis(link)
        elif chapter_content == constants.CONTENT_TRAINING:
            self.generate_training_result(link)
        elif chapter_content == constants.CONTENT_HYPEROPT:
            self.generate_hyperopt_result(link)
        elif chapter_content == constants.CONTENT_RECOMMENDATION:
            self.generate_recommendations(link)
        elif chapter_content == constants.CONTENT_DEEPLEARNING:
            self.generate_deeplearning(link)

    def output_report(self, output_path):
        self.output('%s/%s' % (output_path, constants.PDF_NAME))
        print('Training report generated.')
        if os.path.exists(constants.FIGURE_PATH):
            shutil.rmtree(constants.FIGURE_PATH)

    def setup_report_info(self):
        self.set_report_info(usecase_name=self.report_params.usecase_name, version=self.report_params.usecase_version)
        self.set_author(author=self.report_params.usecase_team)

    def get_model_info(self, model_meta):
        self.my_write_line("Model Information", 'B')

        self.start_itemize()
        self.my_write_key_value("Use case name", self.usecase_name)
        self.my_write_key_value("Version #", self.version)

        if constants.METADATA_PREDICTIVE_SCENARIO in model_meta[constants.METADATA_KEY_PARAM_SEC]:
            self.my_write_key_value("Predictive scenario",
                                    model_meta[constants.METADATA_KEY_PARAM_SEC][
                                        constants.METADATA_PREDICTIVE_SCENARIO])
        if constants.METADATA_MODEL_UUID in model_meta[constants.METADATA_KEY_PARAM_SEC]:
            self.my_write_key_value("Model UUID",
                                    model_meta[constants.METADATA_KEY_PARAM_SEC][constants.METADATA_MODEL_UUID])

        self.end_itemize()

    def get_data_count_summary(self, data_meta, label_key, sample_count):

        all_num = None, ''
        train_num = None, ''
        valid_num = None, ''
        test_num = None, ''
        extend_train_num = None, ''
        extend_valid_num = None, ''
        extend_test_num = None, ''

        # confirm the test data amount
        if constants.KEY_DATA_EXTEND_TEST in data_meta.keys():
            extend_test_num = data_meta[constants.KEY_DATA_EXTEND_TEST][label_key][
                                  constants.KEY_TOTAL_COUNT], '(after processing)'
        elif constants.KEY_DATA_TEST in sample_count:
            extend_test_num = sample_count[constants.KEY_DATA_TEST], '(after processing)'

        # confirm the all data amount
        if constants.KEY_DATA_ALL in data_meta.keys():
            all_num = data_meta[constants.KEY_DATA_ALL][label_key][constants.KEY_TOTAL_COUNT], ''

        if constants.KEY_DATA_EXTEND_TRAIN in data_meta.keys():
            extend_train_num = data_meta[constants.KEY_DATA_EXTEND_TRAIN][label_key][
                                   constants.KEY_TOTAL_COUNT], '(after processing)'
        elif constants.KEY_DATA_TRAIN in sample_count:
            extend_train_num = sample_count[constants.KEY_DATA_TRAIN], '(after processing)'
        elif all_num[0] is not None:
            extend_train_num = (all_num[0] - extend_test_num[0]), '(after processing)'

        if constants.KEY_DATA_EXTEND_VALID in data_meta.keys():
            extend_valid_num = data_meta[constants.KEY_DATA_EXTEND_VALID][label_key][
                                   constants.KEY_TOTAL_COUNT], '(after processing)'

        if all_num[0] is None:
            if (extend_test_num[0] is not None) and (extend_train_num[0] is not None):
                all_num[0] = extend_test_num[0] + extend_train_num[0]

        if constants.KEY_DATA_TRAIN in data_meta.keys():
            train_num = data_meta[constants.KEY_DATA_TRAIN][label_key][constants.KEY_TOTAL_COUNT], '(before processing)'
        if constants.KEY_DATA_VALID in data_meta.keys():
            valid_num = data_meta[constants.KEY_DATA_VALID][label_key][constants.KEY_TOTAL_COUNT], '(before processing)'
        if constants.KEY_DATA_TEST in data_meta.keys():
            test_num = data_meta[constants.KEY_DATA_TEST][label_key][constants.KEY_TOTAL_COUNT], '(before processing)'

        data_summary = dict()
        data_summary[constants.KEY_DATA_ALL] = all_num
        data_summary[constants.KEY_DATA_TRAIN] = train_num
        data_summary[constants.KEY_DATA_VALID] = valid_num
        data_summary[constants.KEY_DATA_TEST] = test_num
        data_summary[constants.KEY_DATA_EXTEND_TRAIN] = extend_train_num
        data_summary[constants.KEY_DATA_EXTEND_VALID] = extend_valid_num
        data_summary[constants.KEY_DATA_EXTEND_TEST] = extend_test_num

        return data_summary

    def get_data_summary(self, data_summary, notes):
        self.my_write_line(notes, 'B')
        self.start_itemize()
        self.my_write_key_value("Number of all samples %s" % data_summary[constants.KEY_DATA_ALL][1],
                                data_summary[constants.KEY_DATA_ALL][0])
        self.my_write_key_value("Number of training samples %s" % data_summary[constants.KEY_DATA_TRAIN][1],
                                data_summary[constants.KEY_DATA_TRAIN][0])
        self.my_write_key_value("Number of validation samples %s" % data_summary[constants.KEY_DATA_VALID][1],
                                data_summary[constants.KEY_DATA_VALID][0])
        self.my_write_key_value("Number of testing samples %s" % data_summary[constants.KEY_DATA_TEST][1],
                                data_summary[constants.KEY_DATA_TEST][0])
        self.my_write_key_value("Number of training samples %s" % data_summary[constants.KEY_DATA_EXTEND_TRAIN][1],
                                data_summary[constants.KEY_DATA_EXTEND_TRAIN][0])
        self.my_write_key_value("Number of validation samples %s" % data_summary[constants.KEY_DATA_EXTEND_VALID][1],
                                data_summary[constants.KEY_DATA_EXTEND_VALID][0])
        self.my_write_key_value("Number of testing samples %s" % data_summary[constants.KEY_DATA_EXTEND_TEST][1],
                                data_summary[constants.KEY_DATA_EXTEND_TEST][0])

        self.end_itemize()

    def get_timing(self, timing):
        self.my_write_line("Training Time:")
        self.start_itemize()
        if constants.KEY_TIMING_FEATURE in timing.keys():
            self.my_write_key_value("Feature Processing",
                                    datetime.timedelta(seconds=timing[constants.KEY_TIMING_FEATURE]))
        if constants.KEY_TIMING_TRAINING in timing.keys():
            self.my_write_key_value("Training Model",
                                    datetime.timedelta(seconds=timing[constants.KEY_TIMING_TRAINING]))
        if constants.KEY_TIMING_EVALUATION in timing.keys():
            self.my_write_key_value("Evaluation Model",
                                    datetime.timedelta(seconds=timing[constants.KEY_TIMING_EVALUATION]))
        self.end_itemize()

    def get_evaluation_result(self, evaluation_result, mode='test'):

        if mode == 'train':
            set_name = 'Training'
            set_key = constants.KEY_DATA_TRAIN
        if mode == 'valid':
            set_name = 'Validation'
            set_key = constants.KEY_DATA_VALID
        if mode == 'test':
            set_name = 'Testing'
            set_key = constants.KEY_DATA_TEST

        self.my_write_line("Evaluation Result (on %s Set)" % (set_name))
        for label_key, label_evaluation_result in evaluation_result.items():
            if set_key not in label_evaluation_result.keys():
                print('Error: Cannot find training result for %s set [%s] in training meta.' % (set_name, set_key))
                return
            if len(evaluation_result) > 1:
                self.my_write_line("(for label <B>'%s'</B>)" % (label_key))
            self.start_itemize()
            for metric_name, metric_value in label_evaluation_result[set_key].items():
                if metric_name != constants.KEY_VIS_RESULT and metric_name != constants.TRAIN_TEST_CM:
                    if type(metric_value) == dict:
                        if 'average' in metric_value.keys():
                            value = "%s (average)" % metric_value['average']
                        else:
                            value = np.mean(np.array(metric_value['class']))
                    else:
                        value = metric_value
                    self.my_write_key_value("%s" % metric_name.capitalize(), value)
            self.end_itemize()
            self.ln(2)

    def get_training_summary(self, training_meta):
        self.my_write_line("Training Summary", 'B')
        self.start_itemize()
        if constants.KEY_TRAINING_MODE in training_meta:
            training_mode = training_meta[constants.KEY_TRAINING_MODE]
            if training_mode == 0:
                training_mode_text = constants.TEXT_TRAININGMODE_DEFAULT
            elif training_mode == 1:
                training_mode_text = constants.TEXT_TRAININGMODE_HYPEROPT_BENCHMARK
            elif training_mode == 2:
                training_mode_text = constants.TEXT_TRAININGMODE_HYPEROPT
            self.my_write_key_value("Training Mode", training_mode_text)

        if constants.KEY_EVALUATION_RESULT in training_meta:
            self.get_evaluation_result(training_meta[constants.KEY_EVALUATION_RESULT], mode='test')
        self.my_write_line(1)

        if constants.KEY_TIMING in training_meta:
            self.get_timing(training_meta[constants.KEY_TIMING])
        else:
            print("Error: cannot find timing key [%s] in the training meta." % constants.KEY_TIMING)
        self.my_write_line(1)
        self.end_itemize()

    def get_sequence_statistics(self, data_meta, sequence_feature_name):
        if constants.KEY_DATA_EXTEND_TRAIN not in data_meta.keys():
            data_key = constants.KEY_DATA_TRAIN
        else:
            data_key = constants.KEY_DATA_EXTEND_TRAIN

        sample_label_key = list(data_meta[data_key].keys())[0]
        numeric_dist = data_meta[data_key][sample_label_key][constants.KEY_LENGTH_FEATURE_DISTRIBUTION][
            '%s_length' % sequence_feature_name]['all']

        self.add_subsubsection("Sample characteristics")
        self.my_write_line("The following statistical features are generated from the training data.")
        self.my_write_key_value("Training sample number",
                                data_meta[constants.KEY_DATA_EXTEND_TRAIN][sample_label_key][constants.KEY_TOTAL_COUNT])
        self.my_write_line("Interaction numbers for samples:")

        self.start_itemize()
        self.my_write_key_value("Mean", numeric_dist['mean'])
        self.my_write_key_value("Min", numeric_dist['min'])
        self.my_write_key_value("Max", numeric_dist['max'])
        self.my_write_key_value("Median", numeric_dist['median'])
        self.my_write_key_value("10th Percentile", numeric_dist['perc_10'])
        self.my_write_key_value("90th Percentile", numeric_dist['perc_90'])

        self.end_itemize()

    def get_missing_value_checking(self, data_meta):
        self.add_subsection("Missing value checking")
        self.my_write_line("This section shows the percentage of sample data with missing values.")
        self.ln()
        table_header = ['Feature', 'Missing Value Count', 'Percentage']

        for _, data_name, data_title in constants.DATASET_LABEL:
            if data_name not in data_meta:
                continue
            sample_label_key = list(data_meta[data_name].keys())[0]
            missing_value_data = data_meta[data_name][sample_label_key][constants.KEY_MISSING_VALUE_COUNTER]
            all_field_count = data_meta[data_name][sample_label_key][constants.KEY_FIELD_COUNTER]
            table_data = []
            for feature_name in all_field_count:
                if feature_name not in missing_value_data:
                    missing_count = 0
                else:
                    missing_count = missing_value_data[feature_name]
                total_count = all_field_count[feature_name]
                table_data.append(
                    [feature_name, "%s / %s" % (missing_count, total_count),
                     "%.2f%%" % (missing_count / total_count * 100)])
            if len(table_data) > 0:
                self.my_write_line(data_title, "B")
                self.draw_table(table_header, table_data, [70, 50, 50])
                self.ln()

    def get_data_summary_from_results(self, training_meta):
        result = training_meta[constants.KEY_EVALUATION_RESULT]
        sample_count = dict()
        for label_key, label_eval in result.items():
            sample_count[label_key] = dict()
            for dataset in [constants.KEY_DATA_TRAIN, constants.KEY_DATA_VALID, constants.KEY_DATA_TEST]:
                if dataset in label_eval:
                    label_dataset_eval = label_eval[dataset]
                    if constants.TRAIN_TEST_CM in label_dataset_eval:
                        if type(label_dataset_eval[constants.TRAIN_TEST_CM]) == dict:
                            cm = label_dataset_eval[constants.TRAIN_TEST_CM]['values']
                        else:
                            cm = label_dataset_eval[constants.TRAIN_TEST_CM]

                        sample_count[label_key][dataset] = sum([sum(l) for l in cm])
        return sample_count

    def generate_cover_page(self, content_list, _report_data):
        self.add_page()
        self.chapter_title(constants.CONTENT_SUMMARY)

        model_meta = _report_data[constants.KEY_MODEL_META]
        data_meta = _report_data[constants.KEY_DATA_META]
        training_meta = _report_data[constants.KEY_TRAINING_META]

        sample_count = self.get_data_summary_from_results(training_meta)

        self.get_model_info(model_meta)
        self.ln(10)

        self.my_write_line('Data Summary', 'B')
        for label_key, label_sample_count in sample_count.items():
            data_summary = self.get_data_count_summary(data_meta, label_key, label_sample_count)
            if len(sample_count) == 1:
                self.get_data_summary(data_summary, "")
            else:
                self.get_data_summary(data_summary, " (for label %s) " % label_key)
        self.ln(10)

        self.get_training_summary(training_meta)
        self.ln(10)

        self.my_write_line("The training report includes following sections:", 'B')

        page_links = []
        for idx, content_page in enumerate(content_list):
            link = self.add_link()
            self.write(10, "  %s  %s" % (idx + 1, content_page), link)
            self.ln()
            page_links.append(link)

        return page_links

    def get_dataset_distribution(self, data_meta, label_description=None):
        self.add_subsubsection("Dataset distributions")
        self.my_write_line("The train/validation/test split distribution are as follows.")
        if label_description is not None:
            self.my_write_key_value("Label Type", label_description)

        table_header = ['', 'Count', 'Distribution']
        table_data = []
        draw_graph = False

        for _, data_name, data_title in constants.DATASET_LABEL:
            if data_name in data_meta.keys():
                for label_key, label_data_metadata in data_meta[data_name].items():
                    if constants.KEY_DATA_DISTRIBUTION in label_data_metadata:
                        if len(dict(label_data_metadata[constants.KEY_DATA_DISTRIBUTION])) >= 3:
                            distribution = 'See below graphs.'
                            draw_graph = True
                        else:
                            distribution = dict(label_data_metadata[constants.KEY_DATA_DISTRIBUTION])
                    else:
                        distribution = 'N.A.'
                    table_data.append(
                        ['%s(%s)' % (data_title, label_key), label_data_metadata[constants.KEY_TOTAL_COUNT],
                         distribution])

        self.ln()
        self.draw_table(table_header, table_data, [80,40,60])

        if draw_graph:
            image_set = dict()
            if constants.KEY_DATA_TRAIN in data_meta.keys():
                for _, data_name, data_title in constants.DATASET_LABEL:
                    if data_name in data_meta.keys():
                        for label_key, label_data_metadata in data_meta[data_name].items():
                            distribution = dict(label_data_metadata[constants.KEY_DATA_DISTRIBUTION])
                            image_path = gg.BarPlot(data=distribution,
                                                    title='%s_%s_data_distribution' % (data_name, label_key),
                                                    x_label='Number of samples', y_label='Category').draw(
                                caption=data_name,
                                ratio=True,
                                limit_length=20)
                            if data_name == constants.KEY_DATA_TRAIN:
                                image_set[0] = image_path
                            if data_name == constants.KEY_DATA_VALID:
                                image_set[1] = image_path
                            if data_name == constants.KEY_DATA_TEST:
                                image_set[2] = image_path

                self.add_grid_images(image_set, graph_constants.ABSOLUTE_LEFT_BIG_3_GRID_SPEC)
            elif constants.KEY_DATA_ALL in data_meta.keys():
                for label_key, label_data_metadata in data_meta[constants.KEY_DATA_ALL].items():
                    distribution = dict(label_data_metadata[constants.KEY_DATA_DISTRIBUTION])
                    image_path = gg.BarPlot(data=distribution,
                                            title='%s_%s_data_distribution' % (data_name, label_key),
                                            x_label='Number of samples', y_label='Category').draw(
                        caption=constants.KEY_DATA_ALL, ratio=True, limit_length=20)
                    if len(distribution) > 20:
                        self.my_write_line(
                            "For label <B>'%s'</B> (top 20 out of %s shown):" % (label_key, len(distribution)))
                    else:
                        self.my_write_line("For label <B>'%s'</B>:" % label_key)
                    self.add_large_image(image_path)

    def get_data_attributes(self, model_meta):
        self.add_subsection("Data attribute")
        self.my_write_line("The data attributes in 'meta.json' are classified as follows.")

        table_header = ['Data Field', 'Attribute/Sequence', 'Data Type', 'Used in Training']

        table_data = []

        def get_datetype_label(type_code):
            for label, possible_values in constants.FEATURE_DATA_TYPE.items():
                if type_code in possible_values:
                    return label

        for feature_name, feature_json in model_meta[constants.METADATA_KEY_DATA_SEC][
            constants.META_KEY_ATTRIBUTE_FEATURE].items():
            if "used" not in feature_json:
                if get_datetype_label(feature_json['type']) is 'Key':
                    used = 'No'
                else:
                    used = 'Yes'
            else:
                if feature_json['used']:
                    used = 'Yes'
                else:
                    used = 'No'

            table_data.append([feature_name, 'Attribute', get_datetype_label(feature_json['type']), used])

        for feature_name, feature_json in model_meta[constants.METADATA_KEY_DATA_SEC][
            constants.META_KEY_SEQUENCE_FEATURE].items():
            if "used" not in feature_json:
                if get_datetype_label(feature_json['type']) is 'Key':
                    used = 'No'
                else:
                    used = 'Yes'
            else:
                if feature_json['used']:
                    used = 'Yes'
                else:
                    used = 'No'

            table_data.append([feature_name, 'Sequence', get_datetype_label(feature_json['type']), used])

        self.draw_table(table_header, table_data, [60, 40, 40, 40])

    def visualize_data_distribution(self, data_meta, sample_key, show_sample_classes):
        self.add_subsection("Feature distribution")
        self.my_write_line("Below are some frequency plot for each features.")

        if sample_key == constants.KEY_DATA_TRAIN:
            dataset_names = [constants.KEY_DATA_TRAIN, constants.KEY_DATA_TEST, constants.KEY_DATA_VALID]
        elif sample_key == constants.KEY_DATA_EXTEND_TRAIN:
            dataset_names = [constants.KEY_DATA_EXTEND_TRAIN, constants.KEY_DATA_EXTEND_VALID,
                             constants.KEY_DATA_EXTEND_TEST]
        elif sample_key == constants.KEY_DATA_ALL:
            dataset_names = [constants.KEY_DATA_ALL]

        colors = dict()

        for sample_label_key in data_meta[sample_key].keys():
            for field_name, field_distribution in data_meta[sample_key][sample_label_key][
                constants.KEY_CATEGORICAL_FEATURE_DISTRIBUTION].items():
                if len(field_distribution['all']) <= 2:
                    LOGGER.info('%s only have less than 2 values, ignore in visualization.' % field_name)
                    continue
                if len(field_distribution['all']) / sum(field_distribution['all'].values()) > 0.5:
                    LOGGER.info('%s is probably a unique feature, ignore in visualization.' % field_name)
                    continue
                self.my_write_line("Feature: %s" % field_name, 'B')
                for _, dataset, dataset_name in constants.DATASET_LABEL:
                    if dataset not in data_meta.keys():
                        continue
                    if dataset not in dataset_names:
                        continue
                    image_set = dict()
                    all_distribution = \
                        data_meta[dataset][sample_label_key][constants.KEY_CATEGORICAL_FEATURE_DISTRIBUTION][field_name]
                    comment = ''
                    for label_name in all_distribution.keys():
                        if label_name not in colors:
                            colors[label_name] = constants.COLOR_PALLETES[len(colors) % len(constants.COLORS)]
                        data_distribution = all_distribution[label_name]

                        if len(data_distribution) > constants.MAXIMUM_NUM_ENUM_DISPLAY:
                            limit_length = constants.MAXIMUM_NUM_ENUM_DISPLAY
                            if label_name == 'all':
                                comment = '(only top %s are displayed out of %s)' % (
                                    constants.MAXIMUM_NUM_ENUM_DISPLAY, len(data_distribution))
                        else:
                            limit_length = None

                        image_path = gg.BarPlot(data=data_distribution,
                                                title='%s_%s_%s_%s' % (
                                                    dataset, sample_label_key, field_name, label_name),
                                                x_label="", y_label=field_name).draw(limit_length=limit_length,
                                                                                     color_palette=colors[label_name])

                        if label_name == 'all':
                            image_set[0] = image_path
                        else:
                            if show_sample_classes:
                                if 1 not in image_set:
                                    image_set[1] = image_path
                                elif 2 not in image_set:
                                    image_set[2] = image_path

                    self.add_grid_images(image_set, graph_constants.ABSOLUTE_LEFT_BIG_3_GRID_SPEC,
                                         caption="- %s %s" % (dataset, comment), style='I')

        colors = dict()
        for sample_label_key in data_meta[sample_key].keys():
            for field_name, field_distribution in data_meta[sample_key][sample_label_key][
                constants.KEY_NUMERIC_FEATURE_DISTRIBUTION].items():
                self.my_write_line("Feature: %s" % field_name, 'B')
                for _, dataset, dataset_name in constants.DATASET_LABEL:
                    if dataset not in data_meta.keys():
                        continue
                    if dataset not in dataset_names:
                        continue
                    all_distribution = data_meta[dataset][sample_label_key][constants.KEY_NUMERIC_FEATURE_DISTRIBUTION][
                        field_name]
                    image_set = dict()
                    table_set = dict()
                    for label_name in all_distribution.keys():
                        if label_name not in colors:
                            colors[label_name] = constants.COLORS[len(colors) % len(constants.COLORS)]
                        data_distribution = all_distribution[label_name]

                        image_path = gg.KdeDistribution(data=data_distribution,
                                                        title='%s_%s_%s_%s' % (
                                                            dataset, sample_label_key, field_name, label_name),
                                                        x_label="", y_label=field_name).draw(color=colors[label_name])

                        table_header = ['Statistical Field', 'Value']
                        table_values = []
                        for key, value in data_distribution.items():
                            if key in ['kde', 'histogram']:
                                continue
                            table_values.append([key, "%.2f" % value])

                        if label_name == 'all':
                            image_set[0] = image_path
                            table_set[0] = (table_header, table_values)
                        else:
                            if show_sample_classes:
                                if 1 not in image_set:
                                    image_set[1] = image_path
                                elif 2 not in image_set:
                                    image_set[2] = image_path
                    if len(image_set) == 1:
                        table_header, table_values = table_set[0]
                        self.add_image_table(image_set[0], table_header, table_values,
                                             graph_constants.IMAGE_TABLE_GRID_SPEC, caption="- %s" % dataset,
                                             style='I')
                    else:
                        self.add_grid_images(image_set, graph_constants.ABSOLUTE_LEFT_BIG_3_GRID_SPEC,
                                             caption="- %s" % dataset,
                                             style='I')

        for sample_label_key in data_meta[sample_key].keys():
            for field_name, field_distribution in data_meta[sample_key][sample_label_key][
                constants.KEY_TEXT_FEATURE_DISTRIBUTION].items():
                self.my_write_line("Feature: %s" % field_name, 'B')
                for _, dataset, dataset_name in constants.DATASET_LABEL:
                    if dataset not in data_meta.keys():
                        continue
                    if dataset not in dataset_names:
                        continue
                    all_distribution = data_meta[dataset][sample_label_key][constants.KEY_TEXT_FEATURE_DISTRIBUTION][
                        field_name]
                    image_set = dict()
                    table_set = dict()
                    for label_name in all_distribution.keys():
                        data_distribution = all_distribution[label_name]
                        image_path = gg.WordCloudGraph(data=data_distribution['tfidf'],
                                                       title='%s_%s_%s_%s' % (
                                                           dataset, sample_label_key, field_name, label_name)).draw()
                        table_header = ['Placeholder', 'Doc Percentage ']
                        table_values = []
                        for w, v in data_distribution['placeholder'].items():
                            table_values.append([w, '%.2f%%' % (v * 100)])
                        if label_name == 'all':
                            image_set[0] = image_path
                            table_set[0] = (table_header, table_values)
                        else:
                            if show_sample_classes:
                                if 1 not in image_set:
                                    image_set[1] = image_path
                                elif 2 not in image_set:
                                    image_set[2] = image_path
                    if len(image_set) == 1:
                        table_values, table_values = table_set[0]
                        self.add_image_table(image_set[0], table_header, table_values,
                                             graph_constants.IMAGE_TABLE_GRID_SPEC,
                                             caption="- %s" % dataset, style='I')
                    else:
                        self.add_grid_images(image_set, graph_constants.ABSOLUTE_LEFT_BIG_3_GRID_SPEC,
                                             caption="- %s" % dataset, style='I')

        colors = dict()
        for sample_label_key in data_meta[sample_key].keys():
            for field_name, field_distribution in data_meta[sample_key][sample_label_key][
                constants.KEY_LENGTH_FEATURE_DISTRIBUTION].items():
                self.my_write_line("Feature: %s" % field_name, 'B')
                for _, dataset, dataset_name in constants.DATASET_LABEL:
                    if dataset not in data_meta.keys():
                        continue
                    if dataset not in dataset_names:
                        continue
                    all_distribution = data_meta[dataset][sample_label_key][constants.KEY_LENGTH_FEATURE_DISTRIBUTION][
                        field_name]
                    image_set = dict()
                    table_set = dict()
                    for label_name in all_distribution.keys():
                        if label_name not in colors:
                            colors[label_name] = constants.COLORS[len(colors) % len(constants.COLORS)]
                        data_distribution = all_distribution[label_name]

                        image_path = gg.KdeDistribution(data=data_distribution,
                                                        title='%s_%s_%s_%s' % (
                                                            dataset, sample_label_key, field_name, label_name),
                                                        x_label="", y_label=field_name).draw(color=colors[label_name])
                        table_header = ['Statistical Field', 'Value']
                        table_values = []
                        for key, value in data_distribution.items():
                            if key in ['kde', 'histogram']:
                                continue
                            table_values.append([key, "%.3f" % (value)])
                        if label_name == 'all':
                            image_set[0] = image_path
                            table_set[0] = (table_header, table_values)
                        else:
                            if show_sample_classes:
                                if 1 not in image_set:
                                    image_set[1] = image_path
                                elif 2 not in image_set:
                                    image_set[2] = image_path

                    if len(image_set) == 1:
                        table_header, table_values = table_set[0]
                        self.add_image_table(image_set[0], table_header, table_values,
                                             graph_constants.IMAGE_TABLE_GRID_SPEC, caption="- %s" % dataset,
                                             style='I')
                    else:
                        self.add_grid_images(image_set, graph_constants.ABSOLUTE_LEFT_BIG_3_GRID_SPEC,
                                             caption="- %s" % dataset,
                                             style='I')

        self.my_write_line("Notes:", "B")
        self.my_write_line(
            "1.  Due to space limit, distribution for only <B>2 sample classes</B> are shown in each feature visualization.")
        self.my_write_line(
            "2.  For categorical features, extreme values are <B>marked in red</B> and not shown in the right scale in order to show the rest values more clearly.")
        self.my_write_line(
            "3.  For numerical features, please pay attention to the y-axis scale, it might be changed to <B>log scale</B> in order to show the overall distribution.")

    def get_feature_ranking_visualization(self, training_meta, importance_threshold):
        feature_ranking = training_meta[constants.KEY_FEATURE_RANKING]
        feature_ranking = [(score, name) for name, score in feature_ranking]

        image_path = gg.FeatureImportance(data=feature_ranking, title='feature_importance').draw(limit_length=20)

        self.add_subsection("Feature Importance Ranking")

        if image_path is not None:
            self.my_write_line("The figure below shows the top 20 important features for the trained model.")
            self.my_write_line(
                "The feature name includes both field name and corresponding value if it is an categorical feature.")
            self.ln()

            self.add_large_image(image_path)

        self.my_write_line("The features which have an importance score larger than %s are listed in the below table." %
                           importance_threshold)
        self.ln()

        table_header = ['Feature', 'Importance']
        table_data = []

        for feature_name, importance in feature_ranking:
            if float(importance) < importance_threshold:
                break

            table_data.append([feature_name, importance])

        self.draw_table(header=table_header, data=table_data, col_width=[140, 30])

    def get_training_metrics_score(self, evaluation_result, label_key, cm_label):
        self.ln(5)
        self.my_write_line("Result for label <B>'%s'</B> " % label_key)
        cm_image_paths = []
        sw_image_paths = []
        rd_image_paths = []
        similar_class_dict = None
        similar_class_img_spec = None

        if len(cm_label) > 2:
            cr = MultiClassificationResult()
            similar_class_dict = dict()
        else:
            cr = BinaryClassificationResult()

        cr.load_results_from_meta(evaluation_result)
        metric_tables = cr.convert_metrics_to_table()
        confusion_matrices = cr.get_confusion_matrices()

        for table_name, table_header, table_data, table_layout in metric_tables:
            self.my_write_line(table_name, 'B')
            self.draw_table(table_header, table_data, table_layout)
            self.ln()

        for split in cr.get_split_list():
            cm_obj = confusion_matrices[split]
            title = '%s_%s_cm' % (split,label_key)
            image_path = gg.HeatMap(data=cm_obj.get_values(), title=title, x_label='Predict',
                                    y_label='True').draw(x_tick=cm_obj.get_labels(), y_tick=cm_obj.get_labels())
            cm_image_paths.append(image_path)
            if similar_class_dict is not None:
                similar_class_dict[split] = cm_obj.get_top_k_similar_classes(k=1)

        for dataset in cr.get_split_list():
            for metric_name in evaluation_result[dataset].keys():
                if metric_name == constants.KEY_VIS_RESULT:
                    title = '%s_swarm' % dataset
                    image_path = gg.ResultProbability(data=evaluation_result[dataset][metric_name], title=title).draw(
                        limit_size=constants.DEFAULT_LIMIT_SIZE)
                    sw_image_paths.append(image_path)

                    title = '%s_reliability' % dataset
                    image_path = gg.ReliabilityDiagram(data=evaluation_result[dataset][metric_name], title=title).draw()
                    rd_image_paths.append(image_path)

        if similar_class_dict is not None:
            key_feature = self.report_params.key_feature
            similar_class_img_spec = []
            for split, value in similar_class_dict.items():
                for base_class, similar_classes in value.items():
                    for similar_class, sub_cm in similar_classes:
                        if base_class == similar_class:
                            continue
                        img_spec = visualize_feature_for_similar_classes(split, label_key, key_feature, base_class,
                                                                         similar_class,
                                                                         sub_cm)
                        similar_class_img_spec.append(
                            ('%s: %s for class %s and %s' % (split, key_feature, base_class, similar_class), img_spec))
        if len(cm_image_paths) > 0:
            if len(cm_image_paths) == 3:
                self.add_grid_images(cm_image_paths, graph_constants.ABSOLUTE_RESULT_3_EQUAL_GRID_SPEC,
                                     caption="Confusion Matrix", style="B")
            if len(cm_image_paths) == 1:
                self.add_grid_images(cm_image_paths, {0: (0, 0, 150, 150)},
                                     caption="Confusion Matrix", style="B")

        if len(sw_image_paths) > 0:
            self.add_grid_images(sw_image_paths, graph_constants.ABSOLUTE_RESULT_3_EQUAL_GRID_SPEC,
                                 caption="Probability Distribution", style="B")

        if len(rd_image_paths) > 0:
            self.add_grid_images(rd_image_paths, graph_constants.ABSOLUTE_RESULT_3_EQUAL_GRID_SPEC,
                                 caption="Reliability Diagram", style="B")

        if similar_class_img_spec is not None and len(similar_class_img_spec) > 0:
            self.add_page()
            self.my_write_line("Similar Class Distribution", "B")
            self.start_itemize()
            for title, image_spec in similar_class_img_spec:
                self.add_grid_images(**image_spec, caption=title, style='I')
            self.end_itemize()

    def generate_data_analysis(self, link=None):
        self.add_page()
        if link is not None:
            self.set_link(link)
        self.add_section(constants.CONTENT_DATA)

        data_meta = self.report_data[constants.KEY_DATA_META]
        model_meta = self.report_data[constants.KEY_MODEL_META]

        self.add_subsection("Statistical Information of Data")
        self.my_write_line(
            "In the following section, some statistical information regarding the training data will be calculated and/or visualized.")
        self.my_write_line(1)

        if self.report_params.sequence_feature_name is None:
            print('Error: no sequence feature found for params.')
        else:
            self.get_sequence_statistics(data_meta, self.report_params.sequence_feature_name)
            self.ln(10)

        self.get_dataset_distribution(data_meta, self.report_params.label_description)
        self.ln(5)

        self.get_data_attributes(model_meta)
        self.ln(10)

        self.add_page()
        self.visualize_data_distribution(data_meta, self.report_params.feature_sample_key,
                                         show_sample_classes=self.report_params.show_sample_classes)

        self.ln(5)
        self.get_missing_value_checking(data_meta)

    def generate_feature_analysis(self, link=None):
        self.add_page()
        if link is not None:
            self.set_link(link)
        self.add_section(constants.CONTENT_FEATURE)

        training_meta = self.report_data[constants.KEY_TRAINING_META]
        self.get_feature_ranking_visualization(training_meta, constants.IMPORTANCE_THRESHOLD)

    def generate_hyperopt_result(self, link=None):
        self.add_page()
        if link is not None:
            self.set_link(link)
        self.add_section(constants.CONTENT_HYPEROPT)

        # search space
        self.add_subsection("Hyperparameter Tuning Search Space")
        self.start_itemize()
        self.my_write_key_value("NumTrees", "(20, 500)")
        self.my_write_key_value("RandomState", "(200, 1000)")
        self.my_write_key_value("MaxFeature", "auto")
        self.my_write_key_value("MinSplit", "2")
        self.my_write_key_value("MaxDepth", "[None, 4, 5, 6]")
        self.end_itemize()

        self.ln(5)

        model_meta = self.report_data[constants.KEY_MODEL_META]
        training_meta = self.report_data[constants.KEY_TRAINING_META]

        # hyperopt history
        training_log = training_meta[constants.KEY_TRAINING_LOG]

        benchmark_metric = util.map_code_to_text_metric(
            model_meta[constants.METADATA_KEY_PARAM_SEC][constants.META_KEY_HYPER_METRIC])
        benchmark_value = model_meta[constants.METADATA_KEY_PARAM_SEC][constants.META_KEY_HYPER_BENCHMARKING]
        search_history = training_log[constants.KEY_HISTORY]

        self.add_subsection("Hyperparameter Tuning History Result")
        self.my_write_line("The metric results from hyperparameter tuning are shown in the figure.")
        self.start_itemize()
        self.my_write_key_value("Benchmark metric", benchmark_metric)
        self.my_write_key_value("Benchmark value", benchmark_value)
        self.end_itemize()
        self.ln()

        image_path = gg.EvaluationLinePlot(data=search_history, title='hyper_history', x_label='Iterations',
                                           y_label='Metrics Score').draw(benchmark_metric=benchmark_metric,
                                                                         benchmark_value=benchmark_value)

        self.add_large_image(image_path)
        self.ln(constants.LARGE_FIGURE_HEIGHT)

        self.ln()

        # best result for hyperopt

        search_best_idx = training_log[constants.KEY_BEST_INDEX]
        benchmark_score = training_log[constants.KEY_BENCHMARK_SCORE]

        self.add_subsection("Best Result from Hyperparameter Tuning")
        self.my_write_key_value("The best iteration is ", "# %s" % search_best_idx)
        self.my_write_line()
        self.my_write_line("Parameters:", 'B')

        self.start_itemize()
        for param_name, param_value in search_history[search_best_idx][constants.KEY_HISTORY_PARAMETERS].items():
            self.my_write_key_value("%s" % param_name, param_value)
        self.end_itemize()

        self.my_write_line()
        self.my_write_line("Validation Results:", 'B')

        self.start_itemize()
        for param_name, param_value in search_history[search_best_idx][constants.KEY_HISTORY_EVALUATION].items():
            if param_name == benchmark_metric:
                self.my_write_key_value("%s" % param_name.capitalize(), "%s (benchmarking metric)" % param_value)
                final_metric_value = param_value
            else:
                self.my_write_key_value("%s" % param_name.capitalize(), "%s" % param_value)
        self.end_itemize()

        self.ln(5)

        self.add_subsection("Hyperparameter Tuning Final Conclusion")

        if benchmark_score == 0:
            self.my_write_line("There is no benchmarking conducted in this training. ")
            self.my_write_line("We will accept the best result from hyperparameter tuning as final parameter set.")
        else:
            if final_metric_value > benchmark_score:
                self.my_write("Hyperparameter tuning best result (%.4f) is better than benchmark score (%.4f)," % (
                    final_metric_value, benchmark_score))
                if final_metric_value > benchmark_value:
                    self.my_write_line(' and it is better than acceptance benchmark scoring (%.4f).' % benchmark_value)
                    self.my_write_line('<BR>We accept it as the final parameter setting for the trained model.')
                else:
                    self.my_write_line(
                        ' but it fails to meet the acceptance benchmark scoring (%.4f).' % benchmark_value)
                    self.my_write_line('We still accept it as the final parameter setting for the trained model, ' \
                                       'but will continue to improve it.')

            else:
                self.my_write("Hyperparameter tuning best result (%.4f) is worse than benchmark score (%.4f), " % (
                    final_metric_value, benchmark_score))

                if final_metric_value > benchmark_value:
                    self.my_write_line(
                        'and benchmarking result is better than acceptance benchmark scoring (%.4f).' % benchmark_value)
                    self.my_write_line('We accept default parameters as the final solution for the trained model.')
                else:
                    self.my_write_line(
                        'but it fails to meet the acceptance benchmark scoring (%.4f).' % benchmark_value)
                    self.my_write_line(
                        'We still accept default parameters as the final solution for the trained model, ' \
                        'but will continue to improve it.')

    def generate_deeplearning(self, link=None):
        self.add_page()
        if link is not None:
            self.set_link(link)
        self.add_section(constants.CONTENT_DEEPLEARNING)
        benchmark_metric = 'f1'
        benchmark_value = 0.8

        training_meta = self.report_data[constants.KEY_TRAINING_META]

        training_log = training_meta[constants.KEY_TRAINING_LOG]

        if constants.KEY_HISTORY in training_log:
            history = training_log[constants.KEY_HISTORY]
            best_epoch = training_log[constants.KEY_BEST_INDEX]

            image_path = gg.EvaluationLinePlot(data=history, title='training_history', x_label='Steps',
                                               y_label='Metrics Score').draw(benchmark_metric=benchmark_metric,
                                                                             benchmark_value=benchmark_value)

            self.add_subsection("Training Epochs")
            self.my_write_line("The metric results from several training epochs are shown in the figure.")

            self.start_itemize()
            self.my_write_key_value("Benchmark metric", benchmark_metric)
            self.my_write_key_value("Benchmark value", benchmark_value)
            self.end_itemize()

            self.ln()
            self.add_large_image(image_path)

            self.ln()
            self.add_subsection("Best Epoch from Training")
            self.my_write_key_value("The best iteration is ", "# %s" % best_epoch)
            self.my_write_line()

            self.my_write_line("Validation Results:", "B")
            self.start_itemize()
            if best_epoch not in history:
                best_epoch = str(best_epoch)
            for param_name, param_value in history[best_epoch][constants.KEY_HISTORY_EVALUATION].items():
                if param_name == benchmark_metric:
                    self.my_write_key_value(param_name.capitalize(), "%s (benchmarking metric)" % param_value)
                else:
                    self.my_write_key_value(param_name.capitalize(), param_value)
            self.end_itemize()
            self.ln(5)

        if constants.KEY_PARAMETERS in training_meta:
            parameters = training_meta[constants.KEY_PARAMETERS]

            self.add_subsection("Model Parameters")
            self.my_write_line(1)
            self.my_write_line("Parameters", 'B')
            self.start_itemize()
            for param_name, param_value in parameters.items():
                self.my_write_key_value(param_name, param_value)
            self.end_itemize()

    def generate_training_result(self, link=None):
        self.add_page()
        if link is not None:
            self.set_link(link)
        self.add_section(constants.CONTENT_TRAINING)

        sample_dataset_key = None
        if constants.KEY_DATA_EXTEND_TRAIN in self.report_data[constants.KEY_DATA_META]:
            sample_dataset_key = constants.KEY_DATA_EXTEND_TRAIN
        elif constants.KEY_DATA_TRAIN in self.report_data[constants.KEY_DATA_META]:
            sample_dataset_key = constants.KEY_DATA_TRAIN
        elif constants.KEY_DATA_ALL in self.report_data[constants.KEY_DATA_META]:
            sample_dataset_key = constants.KEY_DATA_ALL

        training_meta = self.report_data[constants.KEY_TRAINING_META]

        self.add_subsection("Scoring metrics")
        self.my_write_line(
            "This section displays the results of several scoring metrics to evaluate the performance of the model.")
        self.my_write("The metrics used include: <I>precision, recall, f1 score</I>, etc.")

        self.ln(5)

        for label_key, label_eval in training_meta[constants.KEY_EVALUATION_RESULT].items():
            cm_label = list(
                self.report_data[constants.KEY_DATA_META][sample_dataset_key][label_key][
                    constants.KEY_DATA_DISTRIBUTION].keys())

            self.get_training_metrics_score(label_eval, label_key, cm_label)

        if constants.KEY_PARAMETERS in training_meta:
            parameters = training_meta[constants.KEY_PARAMETERS]
            self.add_subsection("Parameters")
            self.my_write_line("The parameter for this training result is as follows:")

            self.start_itemize()
            for params_name, params_value in parameters.items():
                self.my_write_key_value(params_name, params_value)
            self.end_itemize()
            self.ln(10)

    def generate_recommendations(self, link=None):
        self.add_page()
        if link is not None:
            self.set_link(link)
        self.add_section(constants.CONTENT_RECOMMENDATION)

        data_meta = self.report_data[constants.KEY_DATA_META]
        training_meta = self.report_data[constants.KEY_TRAINING_META]

        metric = self.report_params.recommendation_metric
        deeplearning = self.report_params.is_deeplearning
        sample_label_key = list(training_meta[constants.KEY_EVALUATION_RESULT].keys())[0]
        status, train_eval, valid_eval = rec.get_model_fitting_status(
            training_meta[constants.KEY_EVALUATION_RESULT][sample_label_key],
            metric)

        self.add_subsection("Overall Performance")
        self.my_write_line(
            "The evaluation metric for this use case is <B>%s</B>. Training %s is <B>%.4f</B> and validation %s is <B>%.4f</B>." %
            (metric, metric, train_eval, metric, valid_eval))
        self.my_write_line()

        if status == constants.MODEL_STATUS_FITTING:
            self.my_write_line("It indicates that the model is <B>fitting</B>.")
        elif status == constants.MODEL_STATUS_OVERFITTING:
            self.my_write_line("It indicates that the model is <B>overfitting</B>.")

            self.my_write_line("In the case of overfitting, we suggest the following improvements:")
            self.start_itemize()
            self.my_write_line("Train the model with more data.")
            if deeplearning:
                self.my_write_line("Reduce the model complexity by reducing the number of layers or neutrons.")
                self.my_write_line("Stop the training earlier before validation performance decrease.")
                self.my_write_line("Adding in drop-out layer or regularization term.")
            else:
                self.my_write_line("Reduce the model complexity by decreasing MaxSplit, NumTree or MaxDepth.")
                self.my_write_line("Remove unimportant features based on importance ranking.")
            self.end_itemize()
        elif status == constants.MODEL_STATUS_UNDERFITTING:
            self.my_write_line("It indicates that the model is <B>underfitting</B>.")
            self.start_itemize()
            if deeplearning:
                self.my_write_line("Increase the model complexity by adding more layers or neutrons.")
                self.my_write_line("Train the model with more iterations.")
            else:
                self.my_write_line("Increase the model complexity by increasing MaxSampleSplit, NumTrees or MaxDepth.")
                self.my_write_line("Adding in more representative features.")
            self.end_itemize()

        self.my_write_line()
        self.add_subsection("Label Distribution")
        balanced, max_label, unbalanced_labelled = rec.get_training_data_distribution_balance_status(data_meta)

        if balanced:
            self.my_write_line(
                "The number of training samples for different classes are considered as <B>balanced</B> given a threshold of %s."
                % constants.RECOMMEND_UNBALANCED_BENCHMARK)
        else:
            self.my_write_line(
                "The number of training samples for different classes are considered as <B>unbalanced</B> given a threshold of %s."
                % constants.RECOMMEND_UNBALANCED_BENCHMARK)
            self.my_write_line("Please collect more samples for the following classes:")
            self.start_itemize()
            for label, value in unbalanced_labelled:
                self.my_write_line("class <B>%s</B>: %.4f of class <B>%s</B>" % (label, value, max_label))
            self.end_itemize()

        self.my_write_line()
        self.add_subsection("Data Distribution")
        self.add_subsubsection("Training vs Validation")
        status, key_names, cos_sim, normalized_dist_a, normalized_dist_b = rec.get_data_distribution_similar_status(
            data_meta,
            constants.KEY_DATA_EXTEND_TRAIN,
            constants.KEY_DATA_EXTEND_VALID)
        if status is True:
            self.my_write_line(
                "The label distribution between training set and validation set are considered as <B>similar</B>.")
        else:
            self.my_write_line(
                "The label distribution between training set and validation set are considered as <B>not similar</B>.")
            self.my_write_line("Please balance the data to achieve a similar distribution between two datasets.")

            table_data = [['Training'] + ['%.4f' % x for x in normalized_dist_a],
                          ['Validation'] + ['%.4f' % x for x in normalized_dist_b]]
            table_header = ['Label']
            table_header.extend([str(x) for x in key_names])
            col_width = [int(170 / (len(normalized_dist_a) + 1))] * (len(normalized_dist_a) + 1)
            self.draw_table(header=table_header, data=table_data, col_width=col_width)
        self.my_write_line()
        self.add_subsubsection("Training vs Testing")
        status, key_names, cos_sim, normalized_dist_a, normalized_dist_b = rec.get_data_distribution_similar_status(
            data_meta,
            constants.KEY_DATA_EXTEND_TRAIN,
            constants.KEY_DATA_EXTEND_TEST)
        if status is True:
            self.my_write_line(
                "The label distribution between training set and testing set are considered as <B>similar</B>.")
        else:
            self.my_write_line(
                "The label distribution between training set and testing set are considered as <B>not similar</B>.")
            self.my_write_line("Please balance the data to achieve a similar distribution between two datasets.")

            table_data = [['Training'] + ['%.4f' % x for x in normalized_dist_a],
                          ['Testing'] + ['%.4f' % x for x in normalized_dist_b]]
            table_header = ['Label']
            table_header.extend([str(x) for x in key_names])
            col_width = [int(170 / (len(normalized_dist_a) + 1))] * (len(normalized_dist_a) + 1)
            self.draw_table(header=table_header, data=table_data, col_width=col_width)

        self.add_subsection("Feature Distribution")
        unsimilar_features = {}
        sample_label_key = list(data_meta[constants.KEY_DATA_EXTEND_TRAIN].keys())[0]
        for feature_name in data_meta[constants.KEY_DATA_EXTEND_TRAIN][sample_label_key][
            constants.KEY_CATEGORICAL_FEATURE_DISTRIBUTION].keys():
            result = rec.get_feature_distribution_similar_status(
                data_meta, feature_name, constants.KEY_DATA_EXTEND_TRAIN, constants.KEY_DATA_EXTEND_VALID)
            status, key_names, cos_sim, size_a, size_b, overlap = result
            if status is False:
                unsimilar_features[feature_name] = result
        if len(unsimilar_features) > 0:
            self.my_write_line(
                "The following features are considered to have <B>dissimilar</B> distributions between training set and validation set:")
            self.start_itemize()
            for feature_name, result in unsimilar_features.items():
                status, key_names, cos_sim, size_a, size_b, overlap = result
                self.my_write_line(
                    "%s: <B>%s</B> unique types in training, <B>%s</B> unique types in validation, <B>%s</B> in common." % (
                        feature_name, size_a, size_b, overlap))
            self.end_itemize()
        else:
            self.my_write_line(
                "Given a threshold of %s, all features are considered to have a <B>similar</B> distribution between training set and validation set." % constants.RECOMMEND_FEATURE_DISTRIBUTION_DISTANCE_BENCHMARK)

        self.my_write_line()
        if constants.KEY_TRAINING_LOG in training_meta:
            self.add_subsection("Other Candidate Models")
            training_log = training_meta[constants.KEY_TRAINING_LOG]
            best_get, recommendations = rec.get_training_history_suggestion(training_log, metric)

            if best_get is True:
                self.my_write_line('Current selected model is the best over training history.')
            else:
                self.my_write_line(
                    'Other than the current best model based on <B>%s</B>, we found the following candicate models:' % metric)
                self.start_itemize()
                for iter_num, diff_f1, diff_auc, diff_metric in recommendations:
                    self.my_write_line(
                        "Model at # %s: increase of <B>%.2f</B> in F1-score and <B>%.2f</B> in AUC ROC, a decrease of <I>%.2f</I> in %s." % (
                            iter_num, diff_f1, diff_auc, diff_metric, metric))
                self.end_itemize()


def generate_report(data_folder, output_path,
                    training_meta=None):
    ## get report data ready
    _report_data = dict()

    report_params = Params(data_folder)

    _report_data[constants.KEY_DATA_META] = prepare_data_metafile(data_folder, file_params=report_params.file_params)

    with open(os.path.join(data_folder, constants.TRAIN_META_FILE), 'r') as f:
        model_meta = json.load(f)

    _report_data[constants.KEY_MODEL_META] = model_meta
    _report_data[constants.KEY_TRAINING_META] = training_meta

    with open(os.path.join(output_path, 'report_data.json'), 'w') as f:
        json.dump(_report_data, f, cls=JsonSerializable)

    ## generate report
    rg = ReportGenerator(report_params, _report_data)
    rg.generate_report(output_path)
