from file_operations import FileOperations
from file_reporter import FileReporter
from photo_operations import PhotoOperations

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
