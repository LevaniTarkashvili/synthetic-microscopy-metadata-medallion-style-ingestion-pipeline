import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
import random
import datetime
import uuid

NUM_SESSIONS = 3
IMAGES_PER_SESSION = 4

MICROSCOPE_MODELS = ["Zeiss Axio Observer Z1", "Leica SP8 STED", "Nikon Ti2-E", "Olympus FV3000"]
OBJECTIVES = ["10x / 0.30 NA", "20x / 0.75 NA", "40x / 1.30 NA (oil)", "63x / 1.40 NA (oil)"]
FLUOROPHORES = ["DAPI", "FITC", "Cy3", "Cy5", "GFP", "mCherry", "Alexa Fluor 488", "Alexa Fluor 647"]
OPERATORS = ["Dr. Anna Müller", "Dr. Ivan Petrov", "Dr. Sarah Chen", "Dr. Lena Fischer"]
SAMPLE_TYPES = ["HeLa cells", "MCF-7 cells", "Mouse brain slice", "Zebrafish embryo", "HEK293T cells"]
STAINING_PROTOCOLS = ["Immunofluorescence", "FISH", "Live-cell imaging", "FRET", "STORM"]


def rand_float(lo, hi, decimals=3):
    return round(random.uniform(lo, hi), decimals)


def rand_date(start_year=2024):
    start = datetime.datetime(start_year, 1, 1)
    delta = datetime.timedelta(
        days=random.randint(0, 540),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59)
    )
    return (start + delta).strftime("%Y-%m-%dT%H:%M:%S")


def build_xml():
    root = ET.Element("MicroscopyDataset", attrib={
        "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
        "version": "2.1",
        "created": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    })

    ET.SubElement(root, "GenerationDate").text = rand_date()

    instrument_lib = ET.SubElement(root, "InstrumentLibrary")
    for model in MICROSCOPE_MODELS:
        inst = ET.SubElement(instrument_lib, "Instrument", attrib={"id": f"INST_{MICROSCOPE_MODELS.index(model)+1:03d}"})
        ET.SubElement(inst, "Model").text = model
        ET.SubElement(inst, "Manufacturer").text = model.split()[0]
        ET.SubElement(inst, "SerialNumber").text = f"SN-{random.randint(100000, 999999)}"
        ET.SubElement(inst, "Type").text = random.choice(["Confocal", "Widefield", "TIRF", "Light-sheet"])
        ET.SubElement(inst, "LastCalibration").text = rand_date(2024)

    sessions = ET.SubElement(root, "Sessions")

    for s_idx in range(NUM_SESSIONS):
        session_id = f"SES_{uuid.uuid4().hex[:8].upper()}"
        session = ET.SubElement(sessions, "Session", attrib={"id": session_id})

        meta = ET.SubElement(session, "SessionMetadata")
        ET.SubElement(meta, "StartDateTime").text = rand_date()
        ET.SubElement(meta, "Operator").text = random.choice(OPERATORS)
        ET.SubElement(meta, "SampleType").text = random.choice(SAMPLE_TYPES)
        ET.SubElement(meta, "StainingProtocol").text = random.choice(STAINING_PROTOCOLS)
        ET.SubElement(meta, "PassageNumber").text = str(random.randint(3, 35))
        ET.SubElement(meta, "InstrumentRef").text = f"INST_{random.randint(1, len(MICROSCOPE_MODELS)):03d}"

        env = ET.SubElement(session, "EnvironmentalConditions")
        ET.SubElement(env, "Temperature_C").text = str(rand_float(36.8, 37.4, 1))
        ET.SubElement(env, "CO2_Percent").text = str(rand_float(4.8, 5.2, 1))
        ET.SubElement(env, "Humidity_Percent").text = str(rand_float(85.0, 95.0, 1))

        acq = ET.SubElement(session, "AcquisitionSettings")
        obj = ET.SubElement(acq, "Objective")
        chosen_obj = random.choice(OBJECTIVES)
        ET.SubElement(obj, "Description").text = chosen_obj
        magnification = int(chosen_obj.split("x")[0])
        ET.SubElement(obj, "Magnification").text = str(magnification)
        ET.SubElement(obj, "NumericalAperture").text = chosen_obj.split("/")[1].split("NA")[0].strip()
        ET.SubElement(obj, "ImmersionMedium").text = "oil" if "oil" in chosen_obj else "air"

        pixel_size = round(0.0645 / (magnification / 10), 4)
        ET.SubElement(acq, "PixelSize_um").text = str(pixel_size)
        ET.SubElement(acq, "BitDepth").text = str(random.choice([12, 16]))
        ET.SubElement(acq, "Binning").text = random.choice(["1x1", "2x2"])
        ET.SubElement(acq, "ZStackStep_um").text = str(rand_float(0.1, 0.5))

        channels = ET.SubElement(acq, "Channels")
        num_channels = random.randint(2, 4)
        chosen_fluorophores = random.sample(FLUOROPHORES, num_channels)
        laser_lines = [405, 488, 561, 640]
        for ch_idx, fluor in enumerate(chosen_fluorophores):
            ch = ET.SubElement(channels, "Channel", attrib={"index": str(ch_idx)})
            ET.SubElement(ch, "Fluorophore").text = fluor
            ET.SubElement(ch, "ExcitationLaser_nm").text = str(laser_lines[ch_idx % len(laser_lines)])
            ET.SubElement(ch, "EmissionFilter_nm").text = f"{laser_lines[ch_idx % len(laser_lines)] + 30}/{random.choice([40, 50, 60])}"
            ET.SubElement(ch, "LaserPower_mW").text = str(rand_float(0.5, 50.0, 1))
            ET.SubElement(ch, "ExposureTime_ms").text = str(rand_float(50, 800, 1))
            ET.SubElement(ch, "Gain").text = str(rand_float(1.0, 4.0, 2))

        images = ET.SubElement(session, "Images")
        for img_idx in range(IMAGES_PER_SESSION):
            img_id = f"IMG_{uuid.uuid4().hex[:10].upper()}"
            img = ET.SubElement(images, "Image", attrib={"id": img_id})
            ET.SubElement(img, "AcquisitionDateTime").text = rand_date()
            ET.SubElement(img, "Filename").text = f"{session_id}_{img_idx+1:04d}.tif"
            ET.SubElement(img, "FileFormat").text = "OME-TIFF"
            ET.SubElement(img, "FileSizeMB").text = str(rand_float(45.0, 512.0, 1))

            dims = ET.SubElement(img, "Dimensions")
            ET.SubElement(dims, "Width_px").text = str(random.choice([1024, 2048, 4096]))
            ET.SubElement(dims, "Height_px").text = str(random.choice([1024, 2048, 4096]))
            ET.SubElement(dims, "ZSlices").text = str(random.randint(5, 80))
            ET.SubElement(dims, "Timepoints").text = str(random.randint(1, 20))
            ET.SubElement(dims, "Channels").text = str(num_channels)

            pos = ET.SubElement(img, "StagePosition")
            ET.SubElement(pos, "X_um").text = str(rand_float(-5000, 5000))
            ET.SubElement(pos, "Y_um").text = str(rand_float(-5000, 5000))
            ET.SubElement(pos, "Z_um").text = str(rand_float(0, 200))

            qc = ET.SubElement(img, "QualityMetrics")
            ET.SubElement(qc, "FocusScore").text = str(rand_float(0.6, 1.0))
            ET.SubElement(qc, "SignalToNoiseRatio").text = str(rand_float(5.0, 40.0))
            ET.SubElement(qc, "ContrastIndex").text = str(rand_float(0.3, 0.95))
            ET.SubElement(qc, "Saturated_pct").text = str(rand_float(0.0, 2.5))
            ET.SubElement(qc, "PassQC").text = "true" if rand_float(0, 1) > 0.15 else "false"

            analysis = ET.SubElement(img, "AnalysisResults")
            ET.SubElement(analysis, "CellCount").text = str(random.randint(10, 500))
            ET.SubElement(analysis, "MeanIntensity").text = str(rand_float(200, 60000))
            ET.SubElement(analysis, "StdIntensity").text = str(rand_float(50, 8000))
            ET.SubElement(analysis, "MeanCellArea_um2").text = str(rand_float(80, 2500))
            ET.SubElement(analysis, "NuclearDiameter_um").text = str(rand_float(5.0, 20.0))
            ET.SubElement(analysis, "Circularity").text = str(rand_float(0.5, 1.0))

    return root


def prettify(element):
    raw = ET.tostring(element, encoding="unicode")
    return minidom.parseString(raw).toprettyxml(indent="  ")


if __name__ == "__main__":
    NUMBER_OF_FILES = 100
    for i in range(NUMBER_OF_FILES):
        output_path = os.path.join("data", f"{i}.xml")
        root = build_xml()
        pretty_xml = prettify(root)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(pretty_xml)