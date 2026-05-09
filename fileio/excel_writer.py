import pandas as pd


def write_normalized_results(results, output_path, sheet_name='Sheet1'):
    df = pd.DataFrame(results)
    df.to_excel(output_path, index=False, sheet_name=sheet_name)
    print(f"结果已保存至: {output_path}")


def write_matched_results(results, output_path, sheet_name='Sheet1'):
    df = pd.DataFrame(results)
    df.to_excel(output_path, index=False, sheet_name=sheet_name)
    print(f"匹配结果已保存至: {output_path}")


def write_rename_results(results, output_path, sheet_name='Sheet1'):
    df = pd.DataFrame(results)
    df.to_excel(output_path, index=False, sheet_name=sheet_name)
    print(f"重命名结果已保存至: {output_path}")


def write_single_column_normalize(input_path, normalized_names, output_path, sheet_name='Sheet1'):
    df = pd.read_excel(input_path, sheet_name=sheet_name)
    df['规范名称'] = normalized_names
    df.to_excel(output_path, index=False, sheet_name=sheet_name)
    print(f"规范化结果已保存至: {output_path}")