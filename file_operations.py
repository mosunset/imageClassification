import os
from typing import Optional
from file_utils import FileUtils

class FileOperations:
    @staticmethod
    def remove_filemany_files(root_dir: Optional[str] = None) -> int:
        """FileMany用の検索ファイル _filemany.simDB を削除する関数"""
        root_dir = root_dir or os.getcwd()
        target_file = "_filemany.simDB"
        deleted_count = 0

        print(f"検索開始: {root_dir}")

        for root, _, files in os.walk(root_dir):
            for file in files:
                if file == target_file:
                    file_path = os.path.join(root, file)
                    try:
                        os.remove(file_path)
                        deleted_count += 1
                        print(f"削除: {file_path}")
                    except Exception as e:
                        print(f"エラー: {file_path} の削除に失敗しました - {e}")

        print(f"完了: {deleted_count} 件のファイルを削除しました")
        return deleted_count

    @staticmethod
    def sanitize_filenames(root_dir: Optional[str] = None) -> int:
        """ファイル名を正規化する関数"""
        root_dir = root_dir or os.getcwd()
        renamed_count = 0

        for root, _, files in os.walk(root_dir):
            for old_name in files:
                old_path = os.path.join(root, old_name)
                base, ext = os.path.splitext(old_name)

                # 拡張子の小文字化
                ext = ext.lower()

                # 名前を正規化
                normalized_base = FileUtils.normalize_name(base)

                # 元のファイル名に半角全角英数が一つもない場合に備え、空になったら仮名を入れる
                if not normalized_base:
                    normalized_base = "file"

                new_name = normalized_base + ext
                new_path = os.path.join(root, new_name)

                # ファイル名の一意性を確保
                new_path = FileUtils.ensure_unique_path(new_path)

                # 名前が変わったときだけリネーム
                if old_path != new_path:
                    os.rename(old_path, new_path)
                    print(f"リネーム: {old_path} -> {new_path}")
                    renamed_count += 1

        return renamed_count

    @staticmethod
    def sanitize_directories(root_dir: Optional[str] = None) -> int:
        """ディレクトリ名を正規化する関数"""
        root_dir = root_dir or os.getcwd()
        renamed_count = 0

        for root, dirs, _ in os.walk(root_dir, topdown=False):
            for old_dir_name in dirs:
                old_dir_path = os.path.join(root, old_dir_name)

                # 名前を正規化
                normalized_name = FileUtils.normalize_name(old_dir_name)

                # 空になったら仮のディレクトリ名を入れる
                if not normalized_name:
                    normalized_name = "folder"

                new_dir_path = os.path.join(root, normalized_name)

                # ディレクトリ名の一意性を確保
                new_dir_path = FileUtils.ensure_unique_path(new_dir_path, is_directory=True)

                # 変更がある場合のみリネーム
                if old_dir_path != new_dir_path:
                    os.rename(old_dir_path, new_dir_path)
                    print(f"ディレクトリリネーム: {old_dir_path} -> {new_dir_path}")
                    renamed_count += 1

        return renamed_count
