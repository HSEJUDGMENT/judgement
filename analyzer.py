import sys
import argparse
import pandas as pd
from classifier import get_parts
from metadata_extractor import get_metadict


def main():

    parser = argparse.ArgumentParser(description='Анализатор текстов судебных решений')
    parser.add_argument('judgment_file', type=str, help='Введите путь к файлу, который хотите обработать.')
    args = parser.parse_args()

    if len(sys.argv) != 2:
        print('analyzer.py <file.html>')

    print('Загрузка файла...')

    judgment_file_path = args.judgment_file

    with open(judgment_file_path) as f:
        data = f.read()

    metadata = pd.DataFrame.from_dict(get_metadict(data))
    parts = pd.DataFrame.from_dict(get_parts(data))

    output_df = pd.concat([metadata, parts], sort=False)\
                .rename(columns={
                                'date': 'дата',
                                'number': 'номер',
                                'court': 'суд',
                                'region':'регион',
                                'judge': 'судья',
                                'article': 'статья',
                                'accused': 'обвиняемый',
                                'fabula':'фабула',
                                'witness': 'показания свидетелей',
                                'meditation': 'размышления судьи',
                                'prove': 'доказательства'
                                })

    output_name = 'result_{0}.xlsx'.format(str(judgment_file_path.replace('/', '').replace('.html', '')))

    return output_df.to_excel(output_name, index=False), print('Готово. Результат в файле ' + output_name + '.')


if __name__ == "__main__":
    main()

