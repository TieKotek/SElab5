from PySide2.QtWidgets import QApplication, QMessageBox, QFileDialog, QVBoxLayout
from PySide2.QtUiTools import QUiLoader
from PySide2.QtGui import QBrush
from PySide2.QtCore import Qt
from collections import deque
from PySide2.QtWebEngineWidgets import QWebEngineView
import os
import csv
import difflib

def compare_file(path1, path2):
    with open(path1) as file1:
        with open(path2) as file2:
            file1_content = file1.readlines()
            file2_content = file2.readlines()
            file1.close()
            file2.close()

    return difflib.HtmlDiff().make_file(file1_content, file2_content)
    

def path_check(path):
    if not (os.path.exists(os.path.join(path, "equal.csv")) and os.path.exists(os.path.join(path, "inequal.csv"))):
        return False
    with open(os.path.join(path, "equal.csv")) as equal:
        with open(os.path.join(path, "inequal.csv")) as inequal:
            equal_dict = csv.DictReader(equal)
            inequal_dict = csv.DictReader(inequal)
            for row in equal_dict:
                if not os.path.exists(row["file1"]) or not os.path.exists(row["file2"]):
                    return False
            for row in inequal_dict:
                if not os.path.exists(row["file1"]) or not os.path.exists(row["file2"]):
                    return False
            equal.close()
            inequal.close()
    if os.path.exists(os.path.join(path, "suspect.csv")):
        with open(os.path.join(path, "suspect.csv")) as suspect:
            suspect_dict = csv.DictReader(suspect)
            for row in suspect_dict:
                if not os.path.exists(row["file1"]) or not os.path.exists(row["file2"]):
                    return False
    return True

class Window():
    def initialize(self):
        self.file_path = ""
        self.current_line = 0
        self.ui.statusButton.setText("请导入机器比对结果所在文件夹")
        self.ui.current_path.setText("")
        self.equal_list = []
        self.recommend_queue = deque()
        self.ui.inequalButton.setEnabled(False)
        self.ui.equalButton.setEnabled(False)
        self.ui.nxtButton.setEnabled(False)
        self.ui.lastButton.setEnabled(False)
        self.ui.suspectButton.setEnabled(False)
        self.ui.endButton.setEnabled(False)
        self.ui.recommend.setEnabled(False)
        self.ui.csvDisplayer.clear()
        self.ui.webview.setHtml("")
        self.ui.code_label.setText("")

    def set_color(self, line):
        if self.equal_list[line]["status"] == "initial":
            if line == self.current_line:
                self.ui.csvDisplayer.item(line).setBackground(self.cyanBrush)
            else:
                self.ui.csvDisplayer.item(line).setBackground(self.noBrush)

        elif self.equal_list[line]["status"] == "inequal":
            self.ui.csvDisplayer.item(line).setBackground(self.redBrush)

        elif self.equal_list[line]["status"] == "suspect":
            self.ui.csvDisplayer.item(line).setBackground(self.yellowBrush)

    def set_code(self, line):
        file1 = self.equal_list[line]["file1"]
        file2 = self.equal_list[line]["file2"]
        self.ui.code_label.setText(f"Code1:{file1}\tCode2: {file2}")
        html = compare_file(self.equal_list[line]["file1"], self.equal_list[line]["file2"])
        self.ui.webview.setHtml(html)

    def __init__(self):
        self.ui = QUiLoader().load('main.ui')
        self.cyanBrush = QBrush(Qt.cyan) # current row
        self.yellowBrush = QBrush(Qt.yellow) # suspect
        self.redBrush = QBrush(Qt.red) # inequal
        self.noBrush = QBrush()
        self.file_path = ""
        self.current_line = 0
        self.equal_list = []
        self.recommend_queue = deque()
        lay = QVBoxLayout(self.ui.container)
        self.ui.webview = QWebEngineView()
        lay.addWidget(self.ui.webview)
        self.initialize()
        self.ui.importButton.clicked.connect(self.import_file)
        self.ui.nxtButton.clicked.connect(self.next_line)
        self.ui.lastButton.clicked.connect(self.last_line)
        self.ui.equalButton.clicked.connect(self.set_equal)
        self.ui.inequalButton.clicked.connect(self.set_inequal)
        self.ui.suspectButton.clicked.connect(self.set_suspect)
        self.ui.endButton.clicked.connect(self.end_and_save)
        self.ui.csvDisplayer.itemClicked.connect(self.change_line)
        self.ui.recommend.clicked.connect(self.push_recommend)


    def import_file(self):
        self.initialize()
        temp_path = QFileDialog.getExistingDirectory(None, "选取文件夹", os.getcwd())
        if path_check(temp_path):
            self.ui.statusButton.setText("导入成功！")
            self.ui.inequalButton.setEnabled(True)
            self.ui.equalButton.setEnabled(True)
            self.ui.nxtButton.setEnabled(True)
            self.ui.lastButton.setEnabled(True)
            self.ui.suspectButton.setEnabled(True)
            self.ui.endButton.setEnabled(True)
            self.ui.recommend.setEnabled(True)
            self.file_path = temp_path
            self.ui.current_path.setText(temp_path)
            equal_list = []
            with open(os.path.join(temp_path, "equal.csv")) as equal:
                equal_list = list(csv.DictReader(equal))
                equal.close()
                for i in range(len(equal_list)):
                    equal_list[i]["status"] = "initial"
            
            if os.path.exists(os.path.join(temp_path, "suspect.csv")):
                with open(os.path.join(temp_path, "suspect.csv")) as suspect:
                    suspect_list = list(csv.DictReader(suspect))
                    suspect.close()
                    for i in range(len(suspect_list)):
                        suspect_list[i]["status"] = "suspect"
            else: 
                suspect_list = []
            
            self.equal_list = suspect_list + equal_list

            if len(self.equal_list) == 0:
                QMessageBox.about(self.ui,
                '导入错误','当前equal.csv和suspect.csv均为空，不需要进行任何人工比对'
                )
                self.initialize()
                return

            for i in range(len(self.equal_list)):
                self.ui.csvDisplayer.addItem(f'File1: {self.equal_list[i]["file1"]}\nFile2: {self.equal_list[i]["file2"]}\n')
                self.set_color(i)

            self.set_color(self.current_line)
            self.set_code(self.current_line)
            self.ui.csvDisplayer.setCurrentRow(self.current_line)
            self.ui.lastButton.setEnabled(False)
            if len(self.equal_list) == 1:
                self.ui.nxtButton.setEnabled(False)
        else:
            QMessageBox.about(self.ui,
            '导入错误','请检查选择文件夹是否包含equal.csv和inequal.csv\n并检查其内容是否符合要求'
            )
            self.initialize()
    
    def next_line(self):
        if len(self.equal_list) > self.current_line + 1:
            self.current_line += 1
            self.ui.csvDisplayer.setCurrentRow(self.current_line)
            self.set_color(self.current_line)
            self.set_code(self.current_line)
            self.set_color(self.current_line - 1)
            if len(self.equal_list) == self.current_line + 1:
                self.ui.nxtButton.setEnabled(False)
            if self.current_line == 1:
                self.ui.lastButton.setEnabled(True)

    def last_line(self):
        if self.current_line > 0:
            self.current_line -= 1
            self.ui.csvDisplayer.setCurrentRow(self.current_line)
            self.set_color(self.current_line)
            self.set_code(self.current_line)
            self.set_color(self.current_line + 1)
            if len(self.equal_list) == self.current_line + 2:
                self.ui.nxtButton.setEnabled(True)
            if self.current_line == 0:
                self.ui.lastButton.setEnabled(False)
    
    def set_suspect(self):
        if self.equal_list[self.current_line]["status"] != "suspect":
            if len(self.recommend_queue) == 0 or self.recommend_queue[-1] != self.current_line:
                self.recommend_queue.append(self.current_line)     
        self.equal_list[self.current_line]["status"] = "suspect"
        self.set_color(self.current_line)

    def set_inequal(self):
        if self.equal_list[self.current_line]["status"] != "inequal":
            if len(self.recommend_queue) == 0 or self.recommend_queue[-1] != self.current_line:
                self.recommend_queue.append(self.current_line)
        self.equal_list[self.current_line]["status"] = "inequal"
        self.set_color(self.current_line)

    def set_equal(self):
        if self.equal_list[self.current_line]["status"] != "initial":
            if len(self.recommend_queue) == 0 or self.recommend_queue[-1] != self.current_line:
                self.recommend_queue.append(self.current_line)
        self.equal_list[self.current_line]["status"] = "initial"
        self.set_color(self.current_line)
    
    def end_and_save(self):
        with open(os.path.join(self.file_path, "equal.csv"), "w") as equal:
            with open(os.path.join(self.file_path, "inequal.csv"), "a") as inequal:
                with open(os.path.join(self.file_path, "suspect.csv"), "w") as suspect:
                    equal_writer = csv.writer(equal)
                    inequal_writer = csv.writer(inequal)
                    suspect_writer = csv.writer(suspect)
                    equal_writer.writerow(["file1", "file2"])
                    suspect_writer.writerow(["file1", "file2"])
                    for item in self.equal_list:
                        if item["status"] == "inequal":
                            inequal_writer.writerow([item["file1"], item["file2"]])
                        elif item["status"] == "initial":
                            equal_writer.writerow([item["file1"], item["file2"]])
                        else:
                            suspect_writer.writerow([item["file1"], item["file2"]])
                equal.close()
                inequal.close()
                suspect.close()
        self.initialize()

    def change_line(self):
        last = self.current_line
        self.current_line = self.ui.csvDisplayer.currentRow()
        self.set_color(last)
        self.set_color(self.current_line)
        self.set_code(self.current_line)
        if self.current_line == 0:
            self.ui.lastButton.setEnabled(False)
        else:
            self.ui.lastButton.setEnabled(True)
        if self.current_line == len(self.equal_list) - 1:
            self.ui.nxtButton.setEnabled(False)
        else:
            self.ui.nxtButton.setEnabled(True)

    def push_recommend(self):
        if len(self.recommend_queue) == 0:
            self.next_line()
        else:
            last = self.current_line
            self.current_line = self.recommend_queue[0]
            self.recommend_queue.popleft()
            self.set_color(last)
            self.set_color(self.current_line)
            self.ui.csvDisplayer.setCurrentRow(self.current_line)
            self.set_code(self.current_line)
            if self.current_line == 0:
                self.ui.lastButton.setEnabled(False)
            else:
                self.ui.lastButton.setEnabled(True)
            if self.current_line == len(self.equal_list) - 1:
                self.ui.nxtButton.setEnabled(False)
            else:
                self.ui.nxtButton.setEnabled(True)
        
app = QApplication([])
app.setOrganizationName('Nanjing University')
app.setApplicationName('人工比对工具')
window = Window()
window.ui.show()
app.exec_()