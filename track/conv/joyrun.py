from track.utils.fio import read_json
from track.utils.time import format_timestamp
from track.utils.xmlx.tcx import TCX, Activity, Extension, Lap, Trackpt


class JoyrunConverter:
    def __init__(self, data, parse_cadence=False):
        record = data["runrecord"]
        self.record = record
        self.start_time = int(record["starttime"])
        self.end_time = int(record["endtime"])

        self.calories = record["daka"]

        self.parse_lap()

        # Format data for Trackpt
        self.heartrate: list = eval(record["heartrate"])
        stepcontent: list = eval(record["stepcontent"])

        cadence = []
        if parse_cadence:
            for i in stepcontent:
                steps = int(i[0]) + int(i[1])
                cadence.append(int(steps / 10))
        self.cadence = cadence

        try:
            position: list = eval(record["content"].replace("-", ","))
            self.position = [[i[0] / 1000000, i[1] / 1000000] for i in position]
        except Exception:
            self.position = None

    def parse_lap(self):
        # list[distance,time_seconds]
        lap_node: list = self.record["node"]
        lap_node.append([self.record["meter"], self.record["second"]])
        lap_node = [[int(d), int(t)] for d, t in lap_node]
        lap_list: list[Lap] = []
        for i in range(len(lap_node)):
            dis = lap_node[i][0]
            ttime = lap_node[i][1]
            stime = self.start_time
            calories = 0
            if i > 0:
                dis -= lap_node[i - 1][0]
                ttime -= lap_node[i - 1][1]
                stime += lap_node[i - 1][1]
            else:
                calories = self.calories
            lap_list.append(
                Lap(
                    start_time=format_timestamp(stime),
                    total_time=ttime,
                    distance=dis,
                    calories=calories,
                )
            )

        self.lap_node = lap_node
        self.lap_list = lap_list

    def running_outdoor(self):
        interval = 5
        lap_num = 0
        current_lap = self.lap_list[0]
        current_time = self.start_time

        for i, pos in enumerate(self.position[:-1]):
            heart = None
            if i <= len(self.heartrate):
                heart = self.heartrate[i - 1]
            cadence = None
            if i <= len(self.cadence):
                cadence = self.cadence[i - 1]

            point = Trackpt(
                time=format_timestamp(current_time),
                lat=pos[0],
                lon=pos[1],
                bpm=heart,
            )
            tpx = Extension("TPX", cadence=cadence)
            point.extension.append(tpx)

            current_lap.track.append(point)
            current_time += interval
            # Lap num increase
            if current_time - self.start_time > self.lap_node[lap_num][1]:
                lap_num += 1
                if lap_num >= len(self.lap_list):
                    lap_num = len(self.lap_list) - 1
                current_lap = self.lap_list[lap_num]

        current_lap.track.append(
            Trackpt(
                time=format_timestamp(self.end_time),
                lat=self.position[-1][0],
                lon=self.position[-1][1],
                bpm=heart,
            )
        )

        # Merge TCX element
        tcx = TCX()
        activity = Activity(id=format_timestamp(self.start_time))

        for i in self.lap_list:
            activity.append(i)
        tcx.activities.append(activity)

        return tcx

    def running_indoor(self):
        interval = 5
        lap_num = 0
        current_lap = self.lap_list[0]
        current_time = self.start_time

        for i, heart in enumerate(self.heartrate[:-1]):
            cadence = None
            if i <= len(self.cadence):
                cadence = self.cadence[i - 1]

            point = Trackpt(
                time=format_timestamp(current_time),
                bpm=heart,
            )

            tpx = Extension("TPX", cadence=cadence)
            point.extension.append(tpx)

            current_lap.track.append(point)
            current_time += interval
            # Lap num increase
            if current_time - self.start_time > self.lap_node[lap_num][1]:
                lap_num += 1
                if lap_num >= len(self.lap_list):
                    lap_num = len(self.lap_list) - 1
                current_lap = self.lap_list[lap_num]

        current_lap.track.append(
            Trackpt(
                time=format_timestamp(self.end_time),
                bpm=self.heartrate[-1],
            )
        )

        # Merge TCX element
        tcx = TCX()
        activity = Activity(id=format_timestamp(self.start_time))

        for i in self.lap_list:
            activity.append(i)
        tcx.activities.append(activity)
        return tcx

    def tcx(self):
        if self.position:
            return self.running_outdoor()
        else:
            return self.running_indoor()


def convert(raw, out):
    print(raw)
    data = read_json(raw)
    joyrun_data = JoyrunConverter(data)
    tcx = joyrun_data.tcx()
    tcx.write(out)
