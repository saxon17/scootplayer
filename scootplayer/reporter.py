#!/usr/bin/env python2.7

import time


class Reporter(object):
    """Object used to report both periodic statistics and events."""

    player = None
    start_time = 0
    report_file = None
    event_file = None
    stats_file = None
    report = False
    options = None
    run = False

    def __init__(self, player):
        """Initialise files to save reports to."""
        self.player = player
        self.report_file = self.player.open_file('/report.csv')
        self.event_file = self.player.open_file('/event.csv')
        self.stats_file = self.player.open_file('/stats.csv')
        self.start()

    def stop(self):
        """Stop reporting and close file handles."""
        self.report = False
        for file in ['report', 'event', 'stats']:
            try:
                getattr('self.' + file + '_file', 'close')()
            except:
                pass

    def pause(self):
        self.run = False

    def resume(self):
        self.run = True

    def start(self):
        """Start reporting thread."""
        self.start_time = time.time()
        self.player.start_thread(self.reporter)

    def time_elapsed(self):
        """Calculate the time elapsed since the start of reporting."""
        return round(time.time() - self.start_time, 4)

    def reporter(self):
        """Periodic reporting of various stats (every second) to file."""
        time_elapsed = self.time_elapsed()
        if self.run:
            self.player.start_timed_thread(self.player.options.reporting_period,
                self.reporter)
            self.player.analysis()
            if self.player.options.csv:
                self.csv_report(time_elapsed)
        else:
            time.sleep(self.player.options.reporting_period)
            self.reporter()

    def stats(self):
        stats = self.player.retrieve_metric('stats')
        for key, value in stats.items():
            self.stats_file.write(str(key) + ',' + str(value) + '\n')
        self.stats_file.write('startup_delay,' + str(self.startup_delay) + '\n')


    def csv_report(self, time_elapsed):
        try:
            self.report_file.flush()
        except ValueError:
            pass
        try:
            report = self.player.retrieve_metric('report')
            output = (str(time_elapsed) + ","
                      + str(report['download_time_buffer']) + ","
                      + str(report['download_bandwidth']) + ","
                      + str(report['download_id']) + ","
                      + str(report['playback_time_buffer']) + ","
                      + str(report['playback_time_position']) + ","
                      + str(report['playback_bandwidth']) + ","
                      + str(report['playback_id']) + ","
                      + str(self.player.bandwidth) + "\n")
        except AttributeError:
            output = str(time_elapsed) + str(', 0, 0, 0, 0, 0, 0, 0, 0\n')
        try:
            self.report_file.write(output)
        except ValueError:
            pass
        if self.player.options.debug:
            print ("[report] " + output),
        try:
            self.report_file.flush()
        except ValueError:
            pass

    def event(self, action, description):
        """Create a thread to handle event."""
        self.player.start_thread(self.event_thread, args=(action, description))

    def event_thread(self, action, description):
        """Event reporting to file."""
        time_elapsed = self.time_elapsed()
        if action == 'start' and description == 'playback':
            self.startup_delay = time_elapsed
        if self.player.options.csv:
            try:
                self.event_file.flush()
            except ValueError:
                pass
            output = (str(time_elapsed) + "," + str(action) + ","
                      + str(description) + "\n")
            try:
                self.event_file.write(output)
            except ValueError:
                pass
            if self.player.options.debug:
                print ("[event] " + output),
            try:
                self.event_file.flush()
            except ValueError:
                pass
