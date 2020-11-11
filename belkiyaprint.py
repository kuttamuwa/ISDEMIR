import arcpy
import os, json
from pathlib import Path

if not arcpy.env.processorType:
    arcpy.env.processorType == "GPU"
    os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
    arcpy.AddMessage("GPU is being used for the training")
elif arcpy.env.processorType == "CPU":
    arcpy.AddMessage("CPU is being used for the training")
elif arcpy.env.processorType == "GPU":
    os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
    os.environ['CUDA_VISIBLE_DEVICES'] = str(arcpy.env.gpuId)
    arcpy.AddMessage("GPU is being used for the training")
else:
    raise CustomCancelException("Processor type is invalid")

import arcgis
import torch
if torch.cuda.is_available():
    arcgis.env._processorType = arcpy.env.processorType
    arcgis.env._gpuid = arcpy.env.gpuId
    torch.cuda.set_device(arcpy.env.gpuId)
import arcgis.learn
from arcgis.learn import prepare_data

try:
    from fastai.callback import Callback

    HAS_FASTAI = True

except Exception as e:
    HAS_FASTAI = False

import warnings
from fastprogress import fastprogress

arcpy.env.autoCancelling = False
fastprogress.NO_BAR = True
warnings.filterwarnings("ignore")

STRING_SSD = "SSD"
STRING_UNET = "UNET"
STRING_FEATURES = "FEATURE_CLASSIFIER"
STRING_PSPNET = "PSPNET"
STRING_RETINANET = "RETINANET"
STRING_MASKRCNN = "MASKRCNN"

MODEL_WITH_PARAMETERS = [
    STRING_SSD,
    STRING_PSPNET,
    STRING_RETINANET
]

MODEL_CLASS_MAPPING = {
    STRING_SSD: "SingleShotDetector",
    STRING_UNET: "UnetClassifier",
    STRING_FEATURES: "FeatureClassifier",
    STRING_PSPNET: "PSPNetClassifier",
    STRING_RETINANET: "RetinaNet",
    STRING_MASKRCNN: "MaskRCNN"
}

#BACKBONE_MODEL_MAPPING = {
#    "RESNET34": "resnet34",
#    "RESNET50": "resnet50"
#}


class CustomCancelException(Exception):
    """Custom exception for geoprocessing tool cancellations"""
    pass


class ProgressCallback(Callback):

    def __init__(self, model, max_epochs, show_accuracy=True, **kwargs):
        super().__init__()
        self.model = model
        self.max_epochs = max_epochs
        self.show_accuracy = show_accuracy

    def on_train_begin(self, **kwargs):
        arcpy.AddMessage(
            "Learning Rate - {}".format(str(self.model._learning_rate)))
        arcpy.SetProgressor("step", "Training....")
        message_string = "Training Loss\t\tValidation Loss"
        if self.show_accuracy:
            message_string = message_string + "\t\tAccuracy"

        arcpy.AddMessage(message_string)

    def on_epoch_begin(self, **kwargs):
        arcpy.SetProgressorLabel("Epoch {}".format(kwargs.get('epoch') + 1))
        percentage_completed = float(
            kwargs.get('epoch') / self.max_epochs) * 100
        arcpy.SetProgressorPosition(int(percentage_completed))

    def on_epoch_end(self, **kwargs):
        last_loss = kwargs.get("last_loss", "NA")
        last_metrics = kwargs.get("last_metrics", [])
        message_string = f"{last_loss}\t{last_metrics[0]}"

        if self.show_accuracy:
            accuracy = last_metrics[1] if len(last_metrics) > 1 else "NA"
            message_string = message_string + f"\t\t{accuracy}"

        arcpy.AddMessage(message_string)
        if arcpy.env.isCancelled:
            raise CustomCancelException('Tool has been cancelled')


def execute():
    if not HAS_FASTAI:
        raise Exception(
            'fast.ai (version 1.0.54 or above) librarie is not installed. Install it using "conda install fastai=1.0.54".')

    """The source code of the tool."""
    in_folder = arcpy.GetParameterAsText(0)
    out_folder = arcpy.GetParameterAsText(1)
    max_epochs = int(arcpy.GetParameterAsText(2))
    model_type = MODEL_CLASS_MAPPING.get(arcpy.GetParameterAsText(3))
    batch_size = int(arcpy.GetParameterAsText(4))
    arguments = arcpy.GetParameter(5)
    learning_rate = float(abs(arcpy.GetParameter(6))) if arcpy.GetParameter(
        6) else None
    backbone_model = arcpy.GetParameterAsText(7)
    pretrained_model = arcpy.GetParameterAsText(8) if arcpy.GetParameterAsText(
        8) else None
    validation_percentage = (
                float(arcpy.GetParameter(9)) / 100) if arcpy.GetParameter(
        9) else None
    stop_training = arcpy.GetParameter(10)
    freeze = arcpy.GetParameter(12)

    # Prepare Data
    prepare_data_kwargs = {'batch_size': batch_size}
    if validation_percentage:
        prepare_data_kwargs['val_split_pct'] = validation_percentage

    arcpy.AddMessage(f"prepare data kwargs : {prepare_data_kwargs}")
    data_bunch = prepare_data(in_folder, **prepare_data_kwargs)

    # SSD model does not support show accuracy
    if arcpy.GetParameterAsText(3) == STRING_SSD:
        show_accuracy = False
    else:
        show_accuracy = True

    if not pretrained_model:
        kwargs = {}
        if arcpy.GetParameterAsText(3) in MODEL_WITH_PARAMETERS:
            for arg_index in range(arguments.rowCount):
                arg_pair = arguments.getRow(arg_index).split('\'')
                for each in arg_pair:
                    if not each.strip():
                        arg_pair.remove(each)
                if arg_pair[1]:
                    kwargs[arg_pair[0]] = eval(arg_pair[1])

        #kwargs['backbone'] = BACKBONE_MODEL_MAPPING.get(backbone_model)
        kwargs['backbone'] = backbone_model.lower()

        # Create Training Model Object
        training_model = getattr(arcgis.learn, model_type)
        training_model_object = training_model(data_bunch, **kwargs)

    else:
        # Use pretrained_model parameters to override user provided parameters if there is any
        with open(pretrained_model) as pt_in:
            pt = json.load(pt_in)
        model_type = pt['ModelName']
        training_model = getattr(arcgis.learn, model_type)
        training_model_object = training_model.from_model(pretrained_model, data_bunch)

    # If Freeze option is unchecked, the layers in the backbone is also updated
    if not freeze:
        training_model_object.unfreeze()

    training_model_object.fit(
        epochs=max_epochs,
        lr=learning_rate,
        early_stopping=stop_training,
        callbacks=[ProgressCallback(training_model_object, max_epochs,
                                    show_accuracy=show_accuracy)]
    )

    arcpy.SetProgressorLabel("Training Completed")
    arcpy.SetProgressorPosition(100)

    arcpy.ResetProgressor()
    # Save object
    training_model_object.save(out_folder)


if __name__ == '__main__':
    execute()
