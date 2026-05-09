import pandas as pd


def read_excel_mapping(excel_path, sheet_name=0):
    df = pd.read_excel(excel_path, sheet_name=sheet_name, header=None)
    if df.shape[1] < 1:
        raise ValueError("Excel 文件至少需要一列")
    
    data_col = 0
    if df.shape[1] > 1:
        col0_has_data = any(pd.notna(df.iloc[i, 0]) and str(df.iloc[i, 0]).strip() for i in range(min(10, len(df))))
        col1_has_data = any(pd.notna(df.iloc[i, 1]) and str(df.iloc[i, 1]).strip() for i in range(min(10, len(df))))
        
        if not col0_has_data and col1_has_data:
            data_col = 1
    
    pairs = []
    for idx in range(len(df)):
        original = str(df.iloc[idx, data_col]).strip() if pd.notna(df.iloc[idx, data_col]) else ""
        if df.shape[1] > data_col + 1:
            normalized = str(df.iloc[idx, data_col + 1]).strip() if pd.notna(df.iloc[idx, data_col + 1]) else ""
        else:
            normalized = ""
        if original and original != 'nan':
            pairs.append((original, normalized))
    return pairs


def read_normalized_excel(excel_path, sheet_name=0):
    df = pd.read_excel(excel_path, sheet_name=sheet_name)
    if df.shape[1] < 2:
        raise ValueError("Excel 文件至少需要两列：原名称、规范名称")
    
    results = []
    for idx in range(len(df)):
        original = str(df.iloc[idx, 0]).strip() if pd.notna(df.iloc[idx, 0]) else ""
        normalized = str(df.iloc[idx, 1]).strip() if pd.notna(df.iloc[idx, 1]) else ""
        file_type = str(df.iloc[idx, 2]).strip() if df.shape[1] > 2 and pd.notna(df.iloc[idx, 2]) else "file"
        path = str(df.iloc[idx, 3]).strip() if df.shape[1] > 3 and pd.notna(df.iloc[idx, 3]) else ""
        results.append({
            'original': original,
            'normalized': normalized,
            'type': file_type,
            'path': path
        })
    return results


def read_movie_list(excel_path, sheet_name=0):
    df = pd.read_excel(excel_path, sheet_name=sheet_name)
    movies = []
    for idx in range(len(df)):
        movie_name = str(df.iloc[idx, 0]).strip() if pd.notna(df.iloc[idx, 0]) else ""
        if movie_name:
            movies.append(movie_name)
    return movies


def read_single_column(excel_path, sheet_name=0):
    df = pd.read_excel(excel_path, sheet_name=sheet_name)
    filenames = []
    for idx in range(len(df)):
        filename = str(df.iloc[idx, 0]).strip() if pd.notna(df.iloc[idx, 0]) else ""
        filenames.append(filename)
    return filenames