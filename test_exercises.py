import unittest
from types import SimpleNamespace
import numpy as np
from config import Config
from exercise_engine import ExerciseEngine, StarterBaseline, calculate_angle, extract_measurement
from evaluate import form_metrics, match_reps, aggregate


def sample(angle=175, body=175, lean=20, horizontal=5, side='left'):
    return dict(angle=angle, body=body, lean=lean, horizontal=horizontal, side=side)


class EngineTests(unittest.TestCase):
    def drive(self, engine, angles, start=0, **kwargs):
        t = start
        for angle in angles:
            for _ in range(24):
                engine.update(sample(angle=angle, **kwargs), t)
                t += 1/30
        return t

    def test_angle_and_degenerate(self):
        self.assertAlmostEqual(calculate_angle([1,0], np.array([0,0]), [0,1]), 90)
        self.assertAlmostEqual(calculate_angle([0,1], np.array([0,0]), [0,-1]), 180)
        self.assertIsNone(calculate_angle([0,0], np.array([0,0]), [1,1]))

    def test_squat_full_cycle(self):
        e = ExerciseEngine()
        t = self.drive(e, [175,85])
        self.assertEqual(len(e.reps), 0)
        self.drive(e, [175,175], start=t)
        self.assertEqual(len(e.reps), 1)
        self.assertEqual(e.reps[0]['form'], 'dung')

    def test_shallow_can_be_wrong(self):
        e = ExerciseEngine()
        self.drive(e, [175,125,175])
        self.assertEqual(e.reps[0]['reason'], 'SHALLOW')

    def test_squat_lean(self):
        e = ExerciseEngine()
        self.drive(e, [175,85,175], lean=65)
        self.assertEqual(e.reps[0]['reason'], 'LEAN')

    def test_pushup_good_and_bad(self):
        for body, expected in [(175,'dung'),(145,'sai')]:
            e = ExerciseEngine('pushup')
            self.drive(e, [175,75,175], body=body)
            self.assertEqual(e.reps[0]['form'], expected)

    def test_pushup_standing_not_counted(self):
        e = ExerciseEngine('pushup')
        self.drive(e, [175,75,175], horizontal=85)
        self.assertEqual(len(e.reps), 0)

    def test_no_start_down_rep(self):
        e = ExerciseEngine()
        self.drive(e, [85,175])
        self.assertEqual(len(e.reps), 0)

    def test_missing_resets_cycle(self):
        e = ExerciseEngine()
        t = self.drive(e, [175,85])
        e.update(None,t)
        self.drive(e,[175],start=t+1/30)
        self.assertEqual(len(e.reps),0)

    def test_switch_side_resets_cycle(self):
        e = ExerciseEngine()
        t = self.drive(e,[175,85])
        self.drive(e,[175],start=t,side='right')
        self.assertEqual(len(e.reps),0)

    def test_long_gap_resets(self):
        e = ExerciseEngine()
        t = self.drive(e,[175,85])
        self.drive(e,[175],start=t+1)
        self.assertEqual(len(e.reps),0)

    def test_spike_not_rep(self):
        e = ExerciseEngine()
        t = self.drive(e,[175])
        e.update(sample(80),t)
        self.drive(e,[175],start=t+1/30)
        self.assertEqual(len(e.reps),0)

    def test_plank_standing_excluded(self):
        e = ExerciseEngine('plank')
        self.drive(e,[175,175],horizontal=85)
        self.assertEqual(e.plank_seconds,0)

    def test_plank_time_uses_timestamps(self):
        totals=[]
        for fps in (15,30,60):
            e = ExerciseEngine('plank')
            for i in range(2*fps+1):
                e.update(sample(),i/fps)
            totals.append(e.plank_seconds)
            self.assertAlmostEqual(e.plank_seconds,1.7,delta=1/fps+0.001)
        self.assertLess(max(totals)-min(totals),0.08)

    def test_plank_stops_immediately_and_gap_not_added(self):
        e=ExerciseEngine('plank')
        t=self.drive(e,[175,175])
        before=e.plank_seconds
        e.update(sample(body=140),t)
        self.assertEqual(e.plank_seconds,before)
        e.update(None,t+0.1)
        e.update(sample(),t+5)
        self.assertEqual(e.plank_seconds,before)

    def test_timestamp_monotonic(self):
        e=ExerciseEngine()
        e.update(sample(),1)
        with self.assertRaises(ValueError):
            e.update(sample(),1)

    def test_pixel_coordinates_and_visibility(self):
        points=[SimpleNamespace(x=0.1,y=0.1,visibility=0.1,presence=1) for _ in range(33)]
        for i,x,y in [(11,.4,.1),(23,.4,.3),(25,.6,.5),(27,.8,.3)]:
            points[i]=SimpleNamespace(x=x,y=y,visibility=.99,presence=1)
        m=extract_measurement(points,1280,720,'squat',Config())
        expected=calculate_angle([.4*1280,.3*720],np.array([.6*1280,.5*720]),[.8*1280,.3*720])
        self.assertAlmostEqual(m['angle'],expected)
        self.assertNotAlmostEqual(m['angle'],90)
        points[25].visibility=.1
        self.assertIsNone(extract_measurement(points,1280,720,'squat',Config()))


class EvaluationTests(unittest.TestCase):
    def test_unknown_is_false_negative(self):
        m=form_metrics([('dung','unknown'),('sai','sai')])
        self.assertEqual(m['accuracy'],.5)
        self.assertEqual(m['coverage'],.5)
        self.assertEqual(m['per_class']['dung']['recall'],0)

    def test_rep_matching_missing_extra(self):
        t=[dict(end_s=1,form='dung'),dict(end_s=3,form='sai')]
        p=[dict(end_s=1.2,form='dung'),dict(end_s=5,form='sai')]
        r=match_reps(t,p,.5)
        self.assertEqual((r['matched'],r['missed'],r['extra']),(1,1,1))
        self.assertIn(('sai','unknown'),r['pairs'])

    def test_config_invalid(self):
        cfg=Config()
        cfg.squat.down=170
        with self.assertRaises(ValueError):
            cfg.validate()


if __name__=='__main__':
    unittest.main()
