import dataclasses
import shutil
import sys

from functools import partial
from pathlib import Path

from PIL import Image, ImageChops

from PySide2.QtCore import (
    Qt,
)
from PySide2.QtWidgets import (
    QApplication,
    QFileDialog,
    QMainWindow,
)
from PySide2.QtGui import (
    QColor,
)

from yukkuri_utility.core import (
    config,
    pipe as p,
)
from yukkuri_utility.gui import (
    appearance,
    log,
)
from yukkuri_utility.tool.chara2ymm4.chara2ymm4_ui import Ui_MainWindow

APP_NAME = 'キャラ素材を変換する。'
__version__ = '0.2.0'


@dataclasses.dataclass
class ConfigData(config.Data):
    src_dir: str = ''
    dst_dir: str = ''


OTHER = '他'
HAIR = '髪'
EYEBROW = '眉'
EYE = '目'
MOUTH = '口'
FACE = '顔'
BODY = '体'
ALL = '全'
BACK = '後'

PARTS_DICT = {
    ALL: '体',
    FACE: '顔色',
}


@dataclasses.dataclass
class AnimConfigData(config.Data):
    # ミリ秒
    offset: int = 0
    wait: int = 0
    frame_duration: int = 33

    def get_anim_data(self, lst: list):
        anim_list = []
        duration_list = []
        for i, item in enumerate(lst):
            duration = self.frame_duration
            if i == 0:
                duration = self.frame_duration + self.offset
            anim_list.append(item)
            duration_list.append(duration)
        if self.wait != 0:
            anim_list.append(lst[0])
            duration_list.append(self.wait - self.offset)
        return anim_list, duration_list


@dataclasses.dataclass
class Anim2ConfigData(config.Data):
    # ミリ秒
    offset: int = 0
    wait: int = 0
    wait2: int = 0
    frame_duration: int = 33

    def get_anim_data(self, lst: list):
        anim_list = []
        duration_list = []
        for i, item in enumerate(lst):
            duration = self.frame_duration
            if i == 0:
                duration = self.frame_duration + self.offset
            if i == len(anim_list) - 1:
                duration = self.frame_duration + self.wait2
            anim_list.append(item)
            duration_list.append(duration)
        for item in reversed(lst[1:-1]):
            duration = self.frame_duration
            anim_list.append(item)
            duration_list.append(duration)
        if self.wait != 0:
            anim_list.append(lst[0])
            duration_list.append(self.wait - self.offset)
        return anim_list, duration_list


ANIM_DICT = {
    'km': Anim2ConfigData(
        offset=0,
        wait=5500,
        wait2=2000,
        frame_duration=33
    ),
    'ky': Anim2ConfigData(
        offset=0,
        wait=5500,
        wait2=2000,
        frame_duration=33
    ),
    'ke': Anim2ConfigData(
        offset=1000,
        wait=5000,
        wait2=5000,
        frame_duration=33
    ),
    'kp': AnimConfigData(
        offset=0,
        wait=8000,
        frame_duration=33
    ),
    'kt': AnimConfigData(
        offset=1000,
        wait=5500,
        frame_duration=33
    ),
    'ks': Anim2ConfigData(
        offset=2500,
        wait=5500,
        wait2=2000,
        frame_duration=33
    ),
    'kw': AnimConfigData(
        offset=0,
        wait=0,
        frame_duration=33
    ),
    'wa': AnimConfigData(
        offset=0,
        wait=100,
        frame_duration=33
    ),
    'rc': AnimConfigData(
        offset=0,
        wait=200,
        frame_duration=33
    ),
    'rs': AnimConfigData(
        offset=0,
        wait=600,
        frame_duration=33
    ),
}


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowTitle('%s  其ノ%s' % (APP_NAME, __version__))
        self.setWindowFlags(
            Qt.Window
            | Qt.WindowCloseButtonHint
            | Qt.WindowStaysOnTopHint
        )
        self.resize(700, 500)

        # config
        self.config_file: Path = config.CONFIG_DIR.joinpath('%s.json' % APP_NAME)
        self.load_config()

        self.template_dir = config.ROOT_PATH.joinpath('data', 'template', APP_NAME)

        # style sheet
        self.ui.convertButton.setStyleSheet(appearance.ex_stylesheet)

        # event

        self.ui.srcToolButton.clicked.connect(partial(self.toolButton_clicked, self.ui.srcLineEdit))
        self.ui.dstToolButton.clicked.connect(partial(self.toolButton_clicked, self.ui.dstLineEdit))

        self.ui.closeButton.clicked.connect(self.close)
        self.ui.convertButton.clicked.connect(self.convert, Qt.QueuedConnection)

        self.ui.actionOpen.triggered.connect(self.open)
        self.ui.actionSave.triggered.connect(self.save)
        self.ui.actionExit.triggered.connect(self.close)

    def set_data(self, c: ConfigData):
        self.ui.srcLineEdit.setText(c.src_dir)
        self.ui.dstLineEdit.setText(c.dst_dir)

    def get_data(self) -> ConfigData:
        c = ConfigData()
        c.src_dir = self.ui.srcLineEdit.text()
        c.dst_dir = self.ui.dstLineEdit.text()

        return c

    def load_config(self) -> None:
        c = ConfigData()
        if self.config_file.is_file():
            c.load(self.config_file)
        self.set_data(c)

    def save_config(self) -> None:
        config.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        c = self.get_data()
        c.save(self.config_file)

    def open(self, is_template=False) -> None:
        dir_path = str(self.template_dir) if is_template else self.ui.dstLineEdit.text().strip()
        path, _ = QFileDialog.getOpenFileName(
            self,
            'Open File',
            dir_path,
            'JSON File (*.json);;All File (*.*)'
        )
        if path != '':
            file_path = Path(path)
            if file_path.is_file():
                c = self.get_data()
                c.load(file_path)
                self.set_data(c)

    def save(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            'Save File',
            self.ui.dstLineEdit.text().strip(),
            'JSON File (*.json);;All File (*.*)'
        )
        if path != '':
            file_path = Path(path)
            c = self.get_data()
            c.save(file_path)

    def closeEvent(self, event):
        self.save_config()
        super().closeEvent(event)

    def add2log(self, text: str, color: QColor = log.TEXT_COLOR) -> None:
        self.ui.logTextEdit.log(text, color)

    def toolButton_clicked(self, w) -> None:
        path = QFileDialog.getExistingDirectory(
            self,
            'Select Directory',
            w.text(),
        )
        if path != '':
            w.setText(path)

    def convert(self) -> None:
        self.ui.logTextEdit.clear()

        data = self.get_data()

        # src directory check
        src_text = data.src_dir.strip()
        src_dir: Path = Path(src_text)
        if src_dir.is_dir() and src_text != '':
            self.add2log('キャラ素材: %s' % str(src_dir))
        else:
            self.add2log('[ERROR]キャラ素材が存在しません。', log.ERROR_COLOR)
            return

        self.add2log('')  # new line

        # dst directory check
        dst_text = data.dst_dir.strip()
        dst_dir: Path = Path(dst_text)
        if dst_dir.is_dir() and dst_text != '':
            self.add2log('出力先: %s' % str(dst_dir))
        else:
            self.add2log('[ERROR]出力先が存在しません。', log.ERROR_COLOR)
            return

        self.add2log('')  # new line

        # 処理開始
        self.add2log('処理中(前準備)')
        # dataにパーツ、プレフィックスで整理してfileを入れる
        data = {}
        offset_flag = False
        for d in p.pipe(
                src_dir.iterdir(),
                p.filter(p.call.is_dir()),
        ):
            part_data = {}
            for f in p.pipe(
                    d.iterdir(),
                    p.filter(p.call.is_file()),
                    p.filter(lambda x: x.name.endswith('.png')),
                    p.map(str),
                    sorted,
                    p.map(Path),
            ):
                f: Path
                key = f.name.split('.')[0][:2]
                if f.name.startswith(key + 'm') and f.name[len(key) + 1].isdigit():
                    key = f.name[:len(key) + 2]
                if f.name.startswith(key + 'u') and f.name[len(key) + 1].isdigit():
                    key = f.name[:len(key) + 2]
                if f.name[:3].isdigit():
                    key = f.name[:3]
                if key not in part_data:
                    part_data[key] = []
                part_data[key].append(f)
            if len(part_data) > 0:
                data[d.name] = part_data

        # コンバート
        for part in data:
            self.add2log('処理中(変換,%s)' % part)
            for key in data[part]:
                key: str
                f0: Path = data[part][key][0]
                lst: list[Path] = data[part][key]
                # 保存先ディレクトリ
                dir_name = f0.parent.name
                if dir_name in PARTS_DICT:
                    dir_name = PARTS_DICT[dir_name]
                dst_part_dir = dst_dir.joinpath(dir_name)
                dst_part_dir.mkdir(exist_ok=True)
                # 口と目は別処理
                if part in [MOUTH, EYE]:
                    s: str = f0.name.split('.')[0]
                    # 特殊な指定は文字残すように
                    suffix: str = ''
                    if s.endswith('-15'):
                        suffix = '-15'
                        # オフセットの指定ガ存在した
                        offset_flag = True
                    if s.endswith('z'):
                        suffix = '+眉'
                    dst_name = key + suffix
                    for i, f in enumerate(
                            # 口はそのまま、目はリバース
                            lst if part == MOUTH else reversed(lst)
                    ):
                        # コピー先決定
                        dst_file = dst_part_dir.joinpath(
                            # 最後だけ連番を付けない
                            (dst_name if i == len(lst) - 1 else dst_name + '.' + str(i)) + '.png'
                        )
                        # copy
                        shutil.copy(f, dst_file)
                # 他の処理
                else:
                    # 名前決め
                    dst_file_name = f0.name
                    if len(key) == 4 and key[2] == 'm':
                        dst_file_name = key[:2] + part + key[2:4] + f0.name[4:]
                        # 手前に表示したい
                        dst_part_dir = dst_dir.joinpath(OTHER)
                        dst_part_dir.mkdir(exist_ok=True)
                    if len(key) == 4 and key[2] == 'u':
                        dst_file_name = key[:2] + part + key[2:4] + f0.name[4:]
                    if part == ALL:
                        dst_file_name = key + '全体' + f0.name[len(key):]
                    # コピー先決定
                    dst_file = dst_part_dir.joinpath(dst_file_name)
                    # copy
                    shutil.copy(f0, dst_file)
                    # 顔色設定 乗算に
                    if part == FACE:
                        face_setting_file = dst_part_dir.joinpath(dst_file_name.split('.')[0] + '.ini')
                        face_setting_file.write_text('blend=3\n')
                    # アニメーション
                    if len(lst) > 1:
                        images = list(map(lambda file: Image.open(file), lst))
                        duration: int | list[int] = 33

                        # アニメーションの設定があったらimages, durationを設定し直す
                        last = lst[-1]
                        anim_key: str = last.name.split('.')[0][-4:-2]
                        if anim_key in ANIM_DICT:
                            images, duration = ANIM_DICT[anim_key].get_anim_data(images)
                        else:
                            anim_key = ''

                        # file決定
                        dst_anim_file = dst_part_dir.joinpath(
                            dst_file_name.split('.')[0] + anim_key + '.webp'
                        )
                        # save
                        images[0].save(
                            str(dst_anim_file),
                            'webp',
                            lossless=True,
                            save_all=True,
                            append_images=images[1:],
                            optimize=True,
                            duration=duration,
                            loop=0
                        )
        # オフセット用画像を作る
        if offset_flag:
            self.add2log('処理中(変換,オフセット素材)')
            for part in [MOUTH, EYEBROW]:
                dst_part_dir = dst_dir.joinpath(part)
                if not dst_part_dir.is_dir():
                    continue
                for f in p.pipe(
                        dst_part_dir.iterdir(),
                        p.filter(lambda x: x.name.endswith('.png')),
                ):
                    with Image.open(f) as im:
                        offset_im = ImageChops.offset(im, 0, -15)
                        ss = f.name.split('.')
                        ss[0] += 'オフセット-15'
                        dst_file = dst_part_dir.joinpath('.'.join(ss))
                        offset_im.save(dst_file)

        # 透明画像を作る
        self.add2log('処理中(変換,透明素材素材)')
        for d in p.pipe(
                dst_dir.iterdir(),
                p.filter(p.call.is_dir())
        ):
            file_list = p.pipe(
                d.iterdir(),
                p.filter(p.call.is_file()),
                p.filter(lambda x: x.name.endswith('.png')),
                p.map(str),
                sorted,
                p.map(Path),
                list,
            )
            if len(file_list) > 0:
                with Image.open(file_list[0]) as im:
                    space_image = Image.new('RGBA', im.size, (0, 0, 0, 0))
                    dst_file = d.joinpath('透明.png')
                    space_image.save(dst_file)

        self.add2log('')  # new line

        # end
        self.add2log('Done!')


def run() -> None:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setPalette(appearance.palette)
    app.setStyleSheet(appearance.stylesheet)

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    run()
