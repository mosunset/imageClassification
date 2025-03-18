import os
from typing import Dict, Optional

class FileReporter:
    @staticmethod
    def report_file_extensions(root_dir: Optional[str] = None, max_files_to_show: int = 50) -> Dict[str, int]:
        """
        拡張子ごとの件数と割合を表示する関数
        50件以下の拡張子は全ファイルパスも表示
        """
        root_dir = root_dir or os.getcwd()
        extension_counts = {}
        extension_files = {}  # 拡張子ごとのファイルパスを保持する辞書
        total_files = 0

        # 全ファイルを走査
        for root, _, files in os.walk(root_dir):
            for file in files:
                total_files += 1
                _, ext = os.path.splitext(file)
                ext = ext.lower()

                # 拡張子別の件数をカウント
                extension_counts[ext] = extension_counts.get(ext, 0) + 1

                # 拡張子別のファイルパスを記録
                if ext not in extension_files:
                    extension_files[ext] = []
                extension_files[ext].append(os.path.join(root, file))

        if total_files == 0:
            print("ファイルが見つかりませんでした。")
            return {}

        print(f"総ファイル数: {total_files}")

        # 件数の多い順に並べ替え
        sorted_ext_counts = sorted(extension_counts.items(), key=lambda x: x[1], reverse=True)
        for ext, count in sorted_ext_counts:
            percentage = (count / total_files) * 100
            print(f"{ext or '(拡張子なし)'}: {count} 個, {percentage:.2f}%")

            # 50件以下の拡張子は全ファイルパスを表示
            if count <= max_files_to_show:
                print(f"  -- {ext or '(拡張子なし)'}のファイル一覧 --")
                for file_path in sorted(extension_files[ext]):
                    print(f"    {file_path}")
                print()  # 空行で区切り

        return extension_counts
