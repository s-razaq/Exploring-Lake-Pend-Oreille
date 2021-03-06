__author__ = 'Saqib Razaq'

from datetime import date, datetime, timedelta
import tkMessageBox
import sqlite3
import lpoWeb

__version__ = '0.0.1'


class LpoDB():

    def __init__(self, **kwargs):

        self.filename = kwargs.get('filename', 'lpo.db')
        self.table = kwargs.get('table', 'Weather')

        self.db = sqlite3.connect(self.filename)
        self.db.row_factory = sqlite3.Row
        self.db.execute('''CREATE TABLE IF NOT EXISTS {}
                        (Date TEXT, Time TEXT, Status TEXT,
                        Air_Temp FLOAT, Barometric_Press FLOAT,
                        Wind_Speed FLOAT)'''.format(self.table))

    def clear(self):
        """
        Clears out the database by dropping the current table
        :return:
        """
        self.db.execute('DROP TABLE IF EXISTS {}'.format(self.table))

    def close(self):
        """
        Safely close down the database
        :return:
        """
        self.db.close()
        del self.filename

    def get_data_for_range(self, start, end):
        """
        Given a start and end date, return a generator of dicts
        containing all available Air_Temp, Barometric_Press, and Wind_Speed values.
        NOTE - It updates the database as necessary first
        :param start:
        :param end:
        :return:
        """

        dates_to_update = []

        # determine pre-2007 dates to update and append to list
        for year in range(start.year, 2007):
            if list(self._get_status_for_range(date(year, 1, 12), date(year, 1, 12))) == []:
                dates_to_update.append(date(year, 1, 12))

        # determine post-2006 dates tp update and append to list
        if (end.year > 2006) and (start >= date(2007, 1, 1,)):
            temp_start = start
        elif (end.year > 2006) and (start < date(2007, 1, 1)):
            temp_start = date(2007, 1, 1)
        else: # start and end are both pre-2007
            temp_start = end

        # generate a list of dates between temp_start and end
        delta = end - temp_start
        for d in range(delta.days+1):
            dates_to_update.append(temp_start + timedelta(days=d))

        statuses = list(self._get_status_for_range(temp_start, end))

        # remove all dates from dates_to_update that have a completed or partial status
        for entry in statuses:
            if entry['Status'] == 'COMPLETE':
                dates_to_update.remove(datetime.strptime(str(entry['Date']), '%Y-%m-%d').date())
            elif entry['Status'] == 'PARTIAL':
                try: # update for any new data first, then remove from dates_to_update list
                    self._update_data_for_data(datetime.strptime(str(entry['Date']), '%Y-%m-%d').date())
                except:
                    raise
                dates_to_update.remove(datetime.strptime(str(entry['Date']), '%Y-%m-%d').date())

        error_dates = []
        for day in dates_to_update:
            try:
                self._update_data_for_data(day, False)
            except ValueError as e:
                error_dates.append(e)

        if error_dates != []:
            error_message = 'There were problems accessing data from the following dates: '
            for day in error_dates:
                error_message += '\n{}'.format(day)
            tkMessageBox.showwarning(title='Warming', message=error_message)

        # get Air_Temp, Barometric_Press, and Wind_Speed data from specified start/end date range
        cursor = self.db.execute('''SELECT Air_Temp, Barometric_Press, Wind_Speed
                                    FROM {} WHERE Date BETWEEN "{}" AND "{}"'''.format(self.table,
                                                                                   start.strftime('%Y-%m-%d'),
                                                                                   end.strftime('%Y-%m-%d')))

        for row in cursor:
            yield dict(row)

    def _get_status_for_range(self, start, end):
        """
        Given a start and end date, return a generator of dicts
        containing all available Date and Status values
        :param start:
        :param end:
        :return:
        """

        # get Dates/Statuses that already exist in DB
        cursor = self.db.execute('''SELECT DISTINCT Date, Status FROM {}
                                 WHERE Date BETWEEN "{}" and "{}"'''.format(self.table,
                                                                        start.strftime('%Y-%m-%d'),
                                                                        end.strftime('%Y-%m-%d')))

        for row in cursor:
            yield dict(row)

    def _update_data_for_data(self, date, partial):
        """
        Uses lpoWeb module to retrieve data for specified date
        and inserts into new DB entry
        NOTE - use partial parameter to specify if entry already exists
        :param date:
        :param partial:
        :return:
        """

        # clear out any partial data for this entry
        if partial:
            self.db.execute('DELETE FROM {} WHERE Date="{}"'.format(self.table, date.strftime('%Y-%m-%d')))
            self.db.commit()

        try:
            data = lpoWeb.get_data_for_date(date)
        except:
            raise

        for entry in data:
            self.db.execute('''INSERT INTO {} (Date, Time, Status, Air_Temp, Barometric_Press, Wind_Speed)
                            VALUES (?, ?, ?, ?, ?, ?)'''.format(self.table), (entry['Date'].replace("_", "-"),
                                                                              entry['Time'],
                                                                              entry['Status'],
                                                                              entry['Air_Temp'],
                                                                              entry['Barometric_Press'],
                                                                              entry['Wind_Speed']))
            self.db.commit()

