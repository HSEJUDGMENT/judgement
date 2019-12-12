from classifier import get_parts
from metadata_extractor import get_metadict


if __name__ == '__main__':
    with open('data/test.txt') as f:
        data = f.read()

    print(get_metadict(data))
    print(get_parts(data))