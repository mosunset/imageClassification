import os
import re
import unicodedata
from PIL import Image, ExifTags
from typing import Callable, Dict, List, Tuple, Optional, Any
import datetime  # 日付変換用に追加
import openai
import base64
from collections import Counter

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

class PhotoOperations:
    @staticmethod
    def extract_exif(file_path: str) -> Dict[str, Any]:
        """画像ファイルからEXIF情報を抽出する関数"""
        exif_data = {}
        try:
            with Image.open(file_path) as img:
                raw_exif = img._getexif()
                if raw_exif:
                    for tag_id, value in raw_exif.items():
                        tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
                        exif_data[tag_name] = value
        except Exception as e:
            print(f"EXIF抽出エラー: {file_path} - {e}")

        return exif_data

    @staticmethod
    def report_exif(root_dir: Optional[str] = None, output_file: str = "exif_report.txt") -> int:
        """JPEG画像の撮影日情報を収集してファイルに出力する関数"""
        root_dir = root_dir or os.getcwd()
        photo_count = 0

        with open(output_file, "w", encoding="utf-8") as f:
            for root, _, files in os.walk(root_dir):
                for filename in files:
                    if filename.lower().endswith(('.jpg', '.jpeg')):
                        file_path = os.path.join(root, filename)
                        exif_data = PhotoOperations.extract_exif(file_path)

                        if "DateTimeOriginal" in exif_data:
                            f.write(f"{file_path} -> {exif_data['DateTimeOriginal']}\n")
                            photo_count += 1

        print(f"撮影日情報が見つかった写真: {photo_count}枚")
        print(f"レポートが {output_file} に保存されました")

        return photo_count

    @staticmethod
    def report_exif_errors(root_dir: Optional[str] = None, output_file: str = "exif_errors.txt") -> int:
        """JPEG画像のうち、EXIF撮影日情報がないファイルのリストを出力する関数"""
        root_dir = root_dir or os.getcwd()
        error_count = 0
        total_photos = 0

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"# EXIF 撮影日情報がない画像ファイルのリスト\n")
            f.write(f"# 生成日時: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# 検索対象: {root_dir}\n\n")

            for root, _, files in os.walk(root_dir):
                for filename in files:
                    if filename.lower().endswith(('.jpg', '.jpeg')):
                        total_photos += 1
                        file_path = os.path.join(root, filename)
                        exif_data = PhotoOperations.extract_exif(file_path)

                        if "DateTimeOriginal" not in exif_data:
                            # 撮影日情報がない場合のみ記録
                            f.write(f"{file_path}\n")
                            error_count += 1

        print(f"写真ファイル総数: {total_photos}枚")
        print(f"撮影日情報がない写真: {error_count}枚 ({(error_count/total_photos*100 if total_photos > 0 else 0):.2f}%)")
        print(f"エラーリストが {output_file} に保存されました")

        return error_count

    @staticmethod
    def rename_photos_with_date(root_dir: Optional[str] = None) -> int:
        """JPG/JPEGファイルの名前の先頭にEXIF撮影日を追加する関数"""
        root_dir = root_dir or os.getcwd()
        renamed_count = 0
        date_pattern = re.compile(r'^p\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}_')

        for root, _, files in os.walk(root_dir):
            for filename in files:
                if not filename.lower().endswith(('.jpg', '.jpeg')):
                    continue

                # 既に日付形式で始まる場合はスキップ
                if date_pattern.match(filename):
                    continue

                file_path = os.path.join(root, filename)

                # EXIF情報を取得
                exif_data = PhotoOperations.extract_exif(file_path)

                # 撮影日情報がなければスキップ
                if "DateTimeOriginal" not in exif_data:
                    continue

                try:
                    # EXIF日時文字列を解析 (通常形式: "YYYY:MM:DD HH:MM:SS")
                    exif_date = exif_data["DateTimeOriginal"]
                    date_obj = datetime.datetime.strptime(exif_date, '%Y:%m:%d %H:%M:%S')

                    # 新しい形式に変換 "pyyyy-MM-dd_hh-mm-ss_"
                    date_prefix = date_obj.strftime('p%Y-%m-%d_%H-%M-%S_')

                    # 新しいファイル名を作成
                    new_filename = f"{date_prefix}{filename}"
                    new_path = os.path.join(root, new_filename)

                    # 重複を避けるためパスの一意性を確保
                    new_path = FileUtils.ensure_unique_path(new_path)

                    # ファイル名が変わる場合のみリネーム
                    if file_path != new_path:
                        os.rename(file_path, new_path)
                        print(f"リネーム: {file_path} -> {new_path}")
                        renamed_count += 1
                except Exception as e:
                    print(f"リネームエラー: {file_path} - {e}")

        return renamed_count

    @staticmethod
    def organize_photos_by_date(root_dir: Optional[str] = None, target_base_dir: str = "images") -> int:
        """JPG/JPEGファイルをEXIF撮影日に基づいて images/yyyy/MM-dd フォルダに整理する関数"""
        root_dir = root_dir or os.getcwd()
        moved_count = 0
        errors_count = 0
        no_date_count = 0

        # ベースディレクトリの絶対パスを取得
        if os.path.isabs(target_base_dir):
            base_dir = target_base_dir
        else:
            # 相対パスの場合は実行ディレクトリからの相対パスとする
            base_dir = os.path.join(os.getcwd(), target_base_dir)

        print(f"写真の整理を開始します: {root_dir} -> {base_dir}")

        for root, _, files in os.walk(root_dir):
            for filename in files:
                if not filename.lower().endswith(('.jpg', '.jpeg')):
                    continue

                file_path = os.path.join(root, filename)

                # EXIF情報を取得
                exif_data = PhotoOperations.extract_exif(file_path)

                # 撮影日情報がなければスキップ
                if "DateTimeOriginal" not in exif_data:
                    print(f"撮影日なし: {file_path}")
                    no_date_count += 1
                    continue

                try:
                    # EXIF日時文字列を解析 (通常形式: "YYYY:MM:DD HH:MM:SS")
                    exif_date = exif_data["DateTimeOriginal"]
                    date_obj = datetime.datetime.strptime(exif_date, '%Y:%m:%d %H:%M:%S')

                    # フォルダパスを作成 "images/YYYY/MM-DD"
                    year_folder = date_obj.strftime('%Y')
                    day_folder = date_obj.strftime('%m-%d')

                    target_dir = os.path.join(base_dir, year_folder, day_folder)

                    # ターゲットディレクトリが存在しなければ作成
                    os.makedirs(target_dir, exist_ok=True)

                    # ターゲットファイルパス
                    target_path = os.path.join(target_dir, filename)

                    # 重複を避けるためパスの一意性を確保
                    target_path = FileUtils.ensure_unique_path(target_path)

                    # ファイルを移動
                    os.rename(file_path, target_path)
                    print(f"移動: {file_path} -> {target_path}")
                    moved_count += 1

                except Exception as e:
                    print(f"エラー: {file_path} - {e}")
                    errors_count += 1

        print(f"処理完了: {moved_count}枚の写真を整理しました。")
        print(f"撮影日情報なし: {no_date_count}枚")
        print(f"エラー: {errors_count}件")

        return moved_count

    @staticmethod
    def analyze_photo_path_exif_correlation(root_dir: Optional[str] = None, max_photos: int = 100) -> Dict:
        """
        写真のパス名とEXIF情報の関連性を分析する関数
        LLMを使って判定し、複数回の結果から多数決で決定する
        """
        root_dir = root_dir or os.getcwd()
        processed_count = 0
        results_summary = {
            "total_analyzed": 0,
            "has_correlation": 0,
            "no_correlation": 0,
            "path_incorrect": 0,
            "exif_incorrect": 0,
            "details": []
        }

        # ローカルLLMサーバーの設定
        openai.api_base = "http://localhost:1234/v1"
        openai.api_key = ""  # APIキーは空欄でOK

        print(f"写真のパス名とEXIF情報の関連性分析を開始します: {root_dir}")

        for root, _, files in os.walk(root_dir):
            for filename in files:
                if not filename.lower().endswith(('.jpg', '.jpeg')):
                    continue

                if processed_count >= max_photos:
                    break

                file_path = os.path.join(root, filename)

                # EXIF情報を取得
                exif_data = PhotoOperations.extract_exif(file_path)

                # 撮影日情報がなければスキップ
                if "DateTimeOriginal" not in exif_data:
                    continue

                try:
                    # 画像をBase64エンコード
                    with open(file_path, "rb") as image_file:
                        encoded_image = base64.b64encode(image_file.read()).decode('utf-8')

                    # パス情報を取得
                    relative_path = os.path.relpath(file_path, root_dir)
                    path_parts = os.path.normpath(relative_path).split(os.sep)

                    # 主要なEXIF情報を抽出
                    exif_summary = {
                        "DateTimeOriginal": exif_data.get("DateTimeOriginal", ""),
                        "Make": exif_data.get("Make", ""),
                        "Model": exif_data.get("Model", ""),
                        "GPSInfo": "あり" if "GPSInfo" in exif_data else "なし"
                    }

                    # 5回判定を行い、結果を集計
                    judgments = []
                    for _ in range(5):
                        judgment = PhotoOperations._get_llm_judgment(path_parts, filename, exif_summary, encoded_image)  # 画像データは容量削減のため先頭部分のみ
                        judgments.append(judgment)

                    # 多数決で最終判定を決定
                    final_judgment = Counter(judgments).most_common(1)[0][0]

                    # 結果を記録
                    result = {
                        "file_path": file_path,
                        "exif_date": exif_data.get("DateTimeOriginal", ""),
                        "final_judgment": final_judgment,
                        "judgment_counts": dict(Counter(judgments))
                    }

                    results_summary["details"].append(result)
                    results_summary["total_analyzed"] += 1

                    if "関連あり_一致" in final_judgment:
                        results_summary["has_correlation"] += 1
                    elif "関連あり_不一致_パス名不正" in final_judgment:
                        results_summary["has_correlation"] += 1
                        results_summary["path_incorrect"] += 1
                    elif "関連あり_不一致_EXIF不正" in final_judgment:
                        results_summary["has_correlation"] += 1
                        results_summary["exif_incorrect"] += 1
                    else:
                        results_summary["no_correlation"] += 1

                    print(f"分析 {processed_count+1}: {file_path}")
                    print(f"  判定結果: {final_judgment}")
                    print(f"  投票内訳: {dict(Counter(judgments))}")

                    processed_count += 1

                except Exception as e:
                    print(f"エラー: {file_path} - {e}")

        # 集計結果を表示
        print("\n===== 分析結果サマリー =====")
        print(f"分析した写真: {results_summary['total_analyzed']}枚")
        print(f"関連性あり: {results_summary['has_correlation']}枚 ({results_summary['has_correlation']/results_summary['total_analyzed']*100:.1f}%)")
        print(f"関連性なし: {results_summary['no_correlation']}枚")
        print(f"パス名が不正と判断: {results_summary['path_incorrect']}枚")
        print(f"EXIF情報が不正と判断: {results_summary['exif_incorrect']}枚")

        return results_summary

    @staticmethod
    def _get_llm_judgment(path_parts: List[str], filename: str, exif_summary: Dict, image_data: str) -> str:
        """LLMを使ってパス名とEXIF情報の関連性を判定する（画像データも送信）"""
        try:
            # テキストプロンプト部分
            text_prompt = f"""
写真のパス名、ファイル名とEXIF情報を分析し、以下の判断をしてください:
1. パス名/ファイル名とEXIF情報の間に関連性があるか
2. 関連性がある場合、互いに一致しているか
3. 一致していない場合、どちらが間違っていると推測されるか

パス: {'/'.join(path_parts)}
ファイル名: {filename}
EXIF情報:
- 撮影日時: {exif_summary['DateTimeOriginal']}
- メーカー: {exif_summary['Make']}
- モデル: {exif_summary['Model']}
- GPS情報: {exif_summary['GPSInfo']}

画像も添付しています。画像の内容も参考にして判断してください。
特に、写真の被写体や風景と、ファイル名やパスに関連性があるかを確認してください。

以下の形式で回答してください：
"関連あり_一致"
"関連あり_不一致_パス名不正"
"関連あり_不一致_EXIF不正"
"関連なし"
"""
            # OpenAIのマルチモーダルAPIフォーマットに合わせてメッセージを構築
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": text_prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
                    ]
                }
            ]

            completion = openai.ChatCompletion.create(
                model="gemma-3-4b-it",  # または画像対応のモデル名に変更
                messages=messages
            )

            # 応答から判定結果を抽出
            response = completion.choices[0].message.content

            print(f"LLM応答: {response}")

            # 応答から判定カテゴリを抽出
            if "関連あり_一致" in response:
                return "関連あり_一致"
            elif "関連あり_不一致_パス名不正" in response:
                return "関連あり_不一致_パス名不正"
            elif "関連あり_不一致_EXIF不正" in response:
                return "関連あり_不一致_EXIF不正"
            else:
                return "関連なし"

        except Exception as e:
            print(f"LLM通信エラー: {e}")
            return "判定エラー"

def main():
    print("ファイルユーティリティ - 選択してください:")
    print("1: _filemany.simDBファイルを削除")
    print("2: ファイル拡張子レポート生成")
    print("3: ファイル名を正規化")
    print("4: ディレクトリ名を正規化")
    print("5: 写真EXIF情報レポート生成")
    print("6: 写真ファイル名に撮影日を追加")
    print("7: 写真を撮影日に基づいて整理")
    print("8: パス名とEXIF情報の関連性分析")

    choice = input("選択 (1-8): ")

    if choice == "1":
        FileOperations.remove_filemany_files()
    elif choice == "2":
        FileReporter.report_file_extensions()
    elif choice == "3":
        FileOperations.sanitize_filenames()
    elif choice == "4":
        FileOperations.sanitize_directories()
    elif choice == "5":
        PhotoOperations.report_exif()
    elif choice == "6":
        PhotoOperations.rename_photos_with_date()
    elif choice == "7":
        PhotoOperations.organize_photos_by_date()
    elif choice == "8":
        max_photos = int(input("分析する最大写真枚数を入力してください (デフォルト: 100): ") or "100")
        PhotoOperations.analyze_photo_path_exif_correlation(max_photos=max_photos)
    else:
        print("無効な選択です。")

if __name__ == '__main__':
    main()
