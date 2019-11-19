import requests


def crawler(homepage):
    dataset_list = requests.get(homepage+'api/action/package_list').json()
    datasetpage = homepage+'dataset/'
    format_dict = {}
    count = 1
    #with open('format_dict.txt', 'a') as file:
    for dataset in dataset_list.get('result'):
        print(count, datasetpage+dataset)
        #if dataset != 'compras-publicas-do-governo-federal':
        sobre_dataset = requests.get(homepage+f'api/3/action/package_show?id={dataset}').json()
        for format in sobre_dataset.get('result')['resources']:

            if format.get('format') in format_dict:
                # append the new number to the existing array at this slot
                format_dict[format.get('format')] = format_dict[format.get('format')] + 1
            else:
                format_dict[format.get('format')] = 1

        count += 1
    return(format_dict)


def main():
    homepage = input('Enter the Open Data Portal index page: Ex: https://www.datos.gov.py/')
    formats = crawler(homepage)
    print(formats)


if __name__ == "__main__":
    main()
