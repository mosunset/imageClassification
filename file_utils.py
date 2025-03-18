import os
import re
import unicodedata

class FileUtils:
    @staticmethod
    def normalize_name(name: str) -> str:
        """名前を正規化する共通関数"""
        # 全角英数を半角に変換
        name = unicodedata.normalize('NFKC', name)

        # 半角/全角英数以外をアンダースコアに変換
        # \uFF10-\uFF19\uFF21-\uFF3A\uFF41-\uFF5A → ０-９Ａ-Ｚａ-ｚ
        name = re.sub(r'[^0-9A-Za-z\uFF10-\uFF19\uFF21-\uFF3A\uFF41-\uFF5A]+', '_', name)

        # 連続するアンダースコアを1つにまとめる
        name = re.sub(r'_{2,}', '_', name)

        # 末尾と先頭の不要なアンダースコアを削除
        if name.endswith('_'):
            name = name[:-1]
        name = re.sub(r'^_+', '', name)

        # 小文字化
        name = name.lower()

        return name

    @staticmethod
    def ensure_unique_path(path: str, is_directory: bool = False) -> str:
        """パスの一意性を確保する関数"""
        if not os.path.exists(path):
            return path

        directory, name = os.path.split(path)

        # ディレクトリの場合は拡張子がない
        if is_directory:
            base, ext = name, ""
        else:
            base, ext = os.path.splitext(name)

        counter = 1
        new_path = path

        # 同じパスが存在し、かつ大文字小文字の区別なしでも異なる場合は連番を付加
        while os.path.exists(new_path) and os.path.normcase(path) != os.path.normcase(new_path):
            new_name = f"{base}_{counter}{ext}"
            new_path = os.path.join(directory, new_name)
            counter += 1

        return new_path
