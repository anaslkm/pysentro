from struct import unpack
from pathlib import Path
import os
import json

fpath = Path(os.path.dirname(__file__))
conf_path = Path("conf/config.json")

with open(fpath.parent / conf_path) as f:
    conf = json.load(f)


class Telegram:
    def __init__(self, telegram: bytearray):
        self.telegram: bytearray = telegram
        self.sender: bytearray = None
        self.recipient: bytearray = None
        self.contained_type: bytearray = None
        self.rawdata: bytearray = None
        self.data : TelegramData = None
        self.decode_telegram()

    def __repr__(self):
        return f"sentro telegram : {self.sender} -> {self.recipient} : {self.contained_type}"
    
    def _decode_telegram_header_elements(self, pointer):
        item_length = self.telegram[pointer] # 8 bits -> 1 byte -> 1 character
        pointer += 1
        item_format = str(item_length) + "s"
        sender_raw = self.telegram[pointer: pointer + item_length]
        pointer += item_length
        item = unpack(item_format, sender_raw)
        if len(item) > 0:
            item = item[0]
        return item, pointer

    def _decode_data(self, pointer):
        data_length_raw = self.telegram[pointer: pointer + 4] # 32 bits -> 4 bytes
        data_length = int.from_bytes(data_length_raw, byteorder="little", signed=True) # signed integer
        pointer += 4
        data = self.telegram[pointer:pointer + data_length]
        return data
    
    def decode_telegram(self):
        sender, pointer = self._decode_telegram_header_elements(0)
        recipient, pointer = self._decode_telegram_header_elements(pointer)
        contained_type, pointer = self._decode_telegram_header_elements(pointer)
        data = self._decode_data(pointer)
        self.sender = sender
        self.recipient = recipient
        self.contained_type = contained_type
        self.rawdata = data
        self.data = TelegramData(self.rawdata)
        self.data.decode_data()


class TelegramData:
    def __init__(self, data: bytearray) -> None:
        self.data: bytearray = data
        self.conf: dict = conf
        self.nbr_spectra: int = None
        self.spectra_data: list[list[int], list[float]] = None
        self.error_msg: bytearray = None
        self.results: dict = None
        self.channel_name: bytearray = None
        self.spectrum_collection: dict = None

    def _decode_number_of_spectra(self):
        number_spectra_raw = self.data[: 4] # 32 bits -> 4 bytes
        N = int.from_bytes(number_spectra_raw, byteorder="little", signed=True) # signed integer
        return N

    def _decode_measurement_data(self, N):
        pointer = 4
        spectra_data = []
        for _ in range(N):
            spectrum_length_raw = self.data[pointer: pointer + 4] # 32 bits -> 4 bytes
            spectrum_length = int.from_bytes(spectrum_length_raw, byteorder="little", signed=True) # signed integer
            pointer += 4
            spectrum_data = self.data[pointer: pointer + spectrum_length]
            pointer += spectrum_length
            spectra_data.append(spectrum_data)
        return spectra_data, pointer
    
    def _decode_error(self, pointer):
        error_msg_length_raw = self.data[pointer: pointer + 4]
        error_msg_length = int.from_bytes(error_msg_length_raw, byteorder="little", signed=True)
        pointer += 4
        error_msg_raw = self.data[pointer: pointer + error_msg_length]
        error_format = str(error_msg_length) + "s"
        error_msg = unpack(error_format, error_msg_raw)[0]
        pointer += error_msg_length
        return error_msg, pointer
    
    @staticmethod
    def _decode_axis(pointer, spectrum_data):
        axis_length_raw = spectrum_data[pointer: pointer + 4] # 32 bits
        axis_length = int.from_bytes(axis_length_raw, byteorder="little", signed=True) # signed integer
        pointer += 4
        axis_raw = spectrum_data[pointer: pointer + axis_length]
        axis_format = str(axis_length //4) + "f" # single array 32 bits * len(x_axis)
        axis = unpack(axis_format, axis_raw)
        pointer += axis_length
        return axis, pointer
    
    def _decode_spectrum(self, spectrum_data):
        spectrum_type = spectrum_data[0] # 8 bits
        pointer = 1
        if spectrum_type == 0:
            pass
        else:
            x_axis, pointer = self._decode_axis(pointer, spectrum_data)
            y_axis, pointer = self._decode_axis(pointer, spectrum_data)
        return x_axis, y_axis
    
    def _decode_spectrum_data(self, spectra_data):
        spectra_list = []
        for spectrum_data in spectra_data:
            x_axis, y_axis = self._decode_spectrum(spectrum_data)
            spectra_list.append([x_axis, y_axis])
        return spectra_list
    
    def _decode_number_results(self, pointer):
        number_results_raw = self.data[pointer: pointer + 4]
        number_results = int.from_bytes(number_results_raw, byteorder="little", signed=True)
        pointer += 4
        return number_results, pointer
    
    @staticmethod
    def _decode_result_items(raw, pointer, type="string"):
        length = raw[pointer]
        pointer += 1
        item_raw = raw[pointer: pointer + length]
        if type == "string":
            item_format = str(length) + "s"
            item = unpack(item_format, item_raw)[0]
        else:
            item = item_raw
        pointer += length
        return item, pointer
    
    def _decode_result(self, result_raw):
        name, pointer = self._decode_result_items(result_raw, 0)
        caption, pointer = self._decode_result_items(result_raw, pointer)
        type, pointer = self._decode_result_items(result_raw, pointer)
        value, pointer = self._decode_result_items(result_raw, pointer, type="double")
        return {"name": name.decode(), "caption": caption.decode(), "type": type.decode(), "value": float(value.decode())}, pointer

    def _decode_results(self, pointer, M):
        results = []
        for _ in range(M):
            result_length_raw = self.data[pointer: pointer + 4]
            pointer += 4
            result_length = int.from_bytes(result_length_raw, byteorder="little", signed=True)
            result_raw = self.data[pointer: pointer + result_length]
            result = self._decode_result(result_raw)
            pointer += result_length
            results.append(result)
        return results, pointer
    
    def _decode_channel_name(self, pointer):
        channel_name_length_raw = self.data[pointer: pointer + 4]
        channel_name_length = int.from_bytes(channel_name_length_raw, byteorder="little", signed=True)
        pointer += 4
        channel_name_raw = self.data[pointer: pointer + channel_name_length]
        channel_format = str(channel_name_length) + "s"
        channel_name = unpack(channel_format, channel_name_raw)[0]
        pointer += channel_name_length
        return channel_name, pointer
    
    def _extract_spectra_collection(self, pointer):
        spectrum_collection_length_raw = self.data[pointer: pointer + 4]
        spectrum_collection_length = int.from_bytes(spectrum_collection_length_raw, byteorder="little", signed=True)
        pointer += 4
        spectrum_collection = self.data[pointer: pointer + spectrum_collection_length]
        pointer += spectrum_collection_length
        return spectrum_collection, pointer
    
    @staticmethod
    def _decode_spectra_collection(spectra_collection):
        N_raw = spectra_collection[:4]
        N = int.from_bytes(N_raw, byteorder="little", signed=True)
        pointer = 1
        spec_coll = {}
        for _ in range(N):
            spectrum_name = spectra_collection[pointer]
            pointer += 1
            spectrum_length_raw = spectra_collection[pointer: pointer + 4]
            pointer += 4
            spectrum_length = int.from_bytes(spectrum_length_raw, byteorder="little", signed=True)
            spectrum = spectra_collection[pointer: pointer + spectrum_length]
            spec_coll[spectrum_name] = spectrum
        return spec_coll
    
    def decode_data(self):
        N = self._decode_number_of_spectra()
        spectra_data, pointer = self._decode_measurement_data(N)
        spectra_list = self._decode_spectrum_data(spectra_data)
        error_msg, pointer = self._decode_error(pointer)
        M, pointer = self._decode_number_results(pointer)
        results, pointer = self._decode_results(pointer, M)
        channel_name, pointer = self._decode_channel_name(pointer)
        spectrum_collection_data, pointer = self._extract_spectra_collection(pointer)
        spectrum_collection = self._decode_spectra_collection(spectrum_collection_data)

        self.nbr_spectra = N
        self.spectra_data = spectra_list
        self.error_msg = error_msg
        self.results = results
        self.channel_name = channel_name
        self.spectrum_collection = spectrum_collection
