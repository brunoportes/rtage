import requests
import ckanapi
import os

# Dataset origin
from_ckan = input('Digite o nome/IP da máquina de origem (Ex: http://dados.contraosagrotoxicos.org/): ')#The homepage URL where data will
#'http://dados.contraosagrotoxicos.org/'


nome = input('Digite o nome/IP da máquina de destino: (Ex: http://dados.clone.org/)')

# Dataset destination
to_ckan = 'http://'+nome #The homepage URL where data will be load (Ex: http://meuportalckan.com.br/)
apikey = input('Digite a chave da API: ') #'ad1e4fb7-03c9-44d1-8291-d6d7c96226d2' #The CKAN Portal API Key (Generated for CKAN Admin profile)
ckan = ckanapi.RemoteCKAN(to_ckan, apikey=apikey)

#from_ckan = 'http://dados.gov.br/'  #The homepage URL where data will be crawled (Ex: http://meuportalckan.com.br/)
#Retrieving dataset list
pagina = requests.get(from_ckan+'api/action/package_list').json()
base = from_ckan+'dataset/'

#Creating first Organization
try:
    ckan.action.organization_create(title='Laboratório GRECO', name='labgreco', id='labgreco')
except Exception as orgError:
    print(orgError)
    pass

for dataset in pagina.get('result'):#[:5]:
    sobre_dataset = requests.get(f'{from_ckan}api/3/action/package_show?id={dataset}').json()
    print(sobre_dataset)
    #Creating group
    for group in sobre_dataset.get('result')['groups']:
        print(group.get('display_name'))
        try:
            ckan.action.group_create(description=group.get('description'),
                                    display_name=group.get('display_name'),
                                    id=group.get('id'),
                                    image_display_url=group.get('image_display_url'),
                                    name=group.get('name'),
                                    title=group.get('title'))
            print(str(group.get('display_name'))+'. New group registered.')
        except Exception as cadastrado:
            print(str(group.get('display_name'))+'. This group was already registered.')
            pass

    #Creating organization
    try:
        ckan.action.organization_create(
            description=sobre_dataset.get('result')['organization'].get('description'),
            id=sobre_dataset.get('result')['organization'].get('id'),
            name=sobre_dataset.get('result')['organization'].get('name'),
            title=sobre_dataset.get('result')['organization'].get('title'))
        print(str(sobre_dataset.get('result')['organization'].get('title'))+'. Registered.')
    except Exception as cadastrado:
        try:
            print(str(sobre_dataset.get('result')['organization'].get('title'))+'. This organization was already registered.')
        except Exception as nulo:
            print('Organization is Null.')
            pass

    #Creating packages(datasets)
    print(base+dataset)
    try:
        ckan.action.package_create(
            author=sobre_dataset.get('result')['author'],
            groups=sobre_dataset.get('result')['groups'],
            id=sobre_dataset.get('result')['id'],
            isopen=True,
            license_id=sobre_dataset.get('result')['license_id'],
            license_title=sobre_dataset.get('result')['license_title'],
            name=sobre_dataset.get('result')['name'],
            notes=sobre_dataset.get('result')['notes'],
            num_tags=sobre_dataset.get('result')['num_tags'],
            tags=sobre_dataset.get('result')['tags'],
            organization=sobre_dataset.get('result')['organization'],
            #owner_org= sobre_dataset.get('result')['owner_org']  or "labgreco",
            owner_org= sobre_dataset.get('result')['owner_org'],
            title=sobre_dataset.get('result')['title']
            )
    except Exception as packageErro:
        print('Dataset already registered.')
        pass

    # Uploading resources (distributions / documents)
    for loop in range(len(sobre_dataset.get('result')['resources'])):
        url = sobre_dataset.get('result')['resources'][loop].get('url')
        extensao = os.path.splitext(url)[1][1:].lower()
        if extensao == '':
            extensao = 'html'
        package_id = sobre_dataset.get('result')['id']
        resource_id = sobre_dataset.get('result')['resources'][loop].get('id')
        subpagina = f'{to_ckan}dataset/{package_id}/resource/{resource_id}.{extensao}'
        download = requests.get(url, allow_redirects=True)
        open(f'dataset/{resource_id}.{extensao}', 'wb').write(download.content)
        if extensao == 'html':
            try:
                ckan.action.resource_create(
                    package_id = package_id,
                    name = sobre_dataset.get('result')['resources'][loop].get('name'),
                    format = sobre_dataset.get('result')['resources'][loop].get('format'),
                    description = sobre_dataset.get('result')['resources'][loop].get('description'),
                    url = url
            )
            except Exception as packageErro:
                print('Resource already registered.')
                pass
        else:
            try:
                ckan.action.resource_create(
                    package_id = package_id,
                    name = sobre_dataset.get('result')['resources'][loop].get('name'),
                    format = sobre_dataset.get('result')['resources'][loop].get('format'),
                    description = sobre_dataset.get('result')['resources'][loop].get('description'),
                    #url = to_ckan+'dataset/'+package_id+'/resource/'+resource_id+'.'+extensao,
                    upload= open(f'dataset/{resource_id}.{extensao}','rb')
            )
            except Exception as packageErro:
                print('Resource already registered.')
                pass

        #Deleting reource file
        file = resource_id+'.'+extensao
        try:
            os.remove(os.path.join('dataset/', file))
        except:
            print('File can not be delete')
