__author__ = 'Saqib Razaq'

from datetime import date
from urllib2 import urlopen

__version__ = '0.0.1'

BASE_URL = 'http://lpo.dt.navy.mil/data/DM/'


def get_data_for_date(date):

    # use correct accessor method based on date
    if date.year < 2007:
        return _get_data_pre2007(date)
    else:
        return _get_data_post2006(date)


def _get_data_pre2007(date):

    # build the url based on year
    url = '{}/Environmental_Data_{}.txt'.format(BASE_URL, date.year)
    print('Fetching online data for {} (full year)'.format(date.year))

    try:
        year_data = urlopen(url).read().decode(encoding='utf_8').split('\n')
    except:
        raise ValueError(date)
    else:
        year_data.pop(0) # remove first element which contains column header info

    for line in year_data:

        elements = line.split()
        yield dict(Date=elements[0],
                   Time=elements[1],
                   Status='COMPLETE',
                   Air_Temp=elements[5],
                   BarometricPress=elements[7],
                   Wind_Speed=elements[2])


def _get_data_post2006(date):

    # build the url based on date & create data container
    url = '{}/{}/{}'.format(BASE_URL, date.year, str(date).replace('-', '_'))
    data = dict(Air_Temp=[], Barometric_Press=[], Wind_Speed=[])

    print('Fetching online data for {}'.format(date))
    for key in data.keys():
        try:
            data[key] = urlopen('{}/{}'.format(url, key)).read().decode(encoding='utf_8').split('\n')
        except Exception as e:
            raise ValueError(date)
        else:
            data[key].pop() # remove last item which will be an empty string

    # verify length of 3 files are equal
    lengths = []
    for k in data.keys():
        lengths.append(len(data[k]))
    if lengths[1:] != lengths[:-1]:
        raise ValueError(date) # file lengths do not match

    for i in range(len(data['Air_Temp'])):

        # verify timestamps are equal for every related entry in 3 files
        timestamps = []
        for k in data.keys():
            timestamps.append(data[k][i].split()[1])
        if timestamps[1:] != timestamps[:-1]:
            raise ValueError(date) # timestamps for fields do not line up

        yield dict(Date=data['Air_Temp'][i].split()[0],
                   Time=data['Air_Temp'][i].split()[1],
                   Status='PARTIAL' if date == date.today() else 'COMPLETE',
                   Air_Temp=data['Air_Temp'][i].split()[2],
                   Barometric_Press=data['Barometric_Press'][i].split()[2],
                   Wind_Speed=data['Wind_Speed'][i].split()[2])


def test():
    pass


if __name__ == '__main__':
    test()
