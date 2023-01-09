# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.

from unittest import TestCase

import numpy as np
from ryvencore.utils import deserialize, serialize

from ironflow.model import dtypes


class TestIsiterable(TestCase):
    def test_isiterable(self):
        self.assertTrue(dtypes.isiterable([0]))
        self.assertTrue(dtypes.isiterable((1, 2, 3)))
        self.assertTrue(dtypes.isiterable(np.array([4, 5])))
        self.assertTrue(dtypes.isiterable("Strings are"))
        self.assertFalse(dtypes.isiterable(42))


class TestDTypes(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.subset = [int, float]
        cls.superset = [int, float, str]

    def test_from_string(self):
        self.assertEqual(dtypes.Data, dtypes.DType.from_str("DType.Data"))

    def test_serialization(self):
        default = "foo"
        items = ["bar", default]
        allow_none = True
        valid_classes = str
        batched = True
        choice = dtypes.Choice(
            default=default,
            items=items,
            valid_classes=valid_classes,
            allow_none=allow_none,
            batched=batched,
        )
        reloaded = dtypes.Choice(_load_state=deserialize(serialize(choice.get_state())))
        self.assertEqual(choice.default, reloaded.default)
        self.assertEqual(choice.items, reloaded.items)
        self.assertEqual(choice.allow_none, reloaded.allow_none)
        self.assertEqual(choice.valid_classes, reloaded.valid_classes)
        self.assertEqual(choice.batched, reloaded.batched)

    def test_untyped(self):
        untyped = dtypes.Untyped()
        with self.subTest("Test untyped input"):
            self.assertTrue(untyped.accepts(7))
            self.assertTrue(untyped.accepts(None))

            untyped.batched = True
            self.assertTrue(untyped.accepts([1, 2, 3]))
            self.assertTrue(untyped.accepts([1, None, 3]))
            self.assertTrue(untyped.accepts("Strings are iterable"))

        data = dtypes.Data(valid_classes=[int, str])
        with self.assertRaises(
                ValueError,
                msg="Checks against untyped should always be by value instead"
        ):
            data.accepts(untyped)

        with self.assertRaises(
                ValueError,
                msg="Untyped should never check against dtypes, but should always be "
                    "checked by value instead"
        ):
            untyped.accepts(data)

    def test_data(self):
        d = dtypes.Integer()
        with self.subTest("Value checking"):
            self.assertTrue(d.accepts(7), msg="Value should match")
            self.assertFalse(d.accepts([]), msg="Value should not match")

        with self.subTest("Dtype checking"):
            self.assertTrue(
                d.accepts(dtypes.Integer()),
                msg="Should match -- identical"
            )
            self.assertTrue(
                d.accepts(dtypes.Data(valid_classes=int)),
                msg="Should match -- dtypes are parent-child related and other valid "
                    "classes are a subset"
            )
            self.assertFalse(
                d.accepts(dtypes.String),
                msg="Should not match -- dtypes are not parent-child (and valid "
                    "classes don't match"
            )
            self.assertFalse(
                d.accepts(dtypes.List(valid_classes=d.valid_classes)),
                msg="Should not match even though valid classes are the same -- dtypes "
                    "are not parent-child"
            )

        with self.subTest("Test valid class sub- and supersets"):
            self.assertTrue(
                dtypes.Data(valid_classes=self.superset).accepts(
                    dtypes.Data(valid_classes=self.subset)
                ),
                msg="DTypes should match when classes are a subset"
            )
            self.assertFalse(
                dtypes.Data(valid_classes=self.subset).accepts(
                    dtypes.Data(valid_classes=self.superset)
                ),
                msg="DTypes should not match when classes are a superset"
            )

    def test_batched_data(self):
        valid_classes = [TestCase, str]
        data = dtypes.Data(valid_classes=valid_classes)
        batch_data = dtypes.Data(valid_classes=valid_classes, batched=True)
        batch_none = dtypes.Data(
            valid_classes=valid_classes, batched=True, allow_none=True
        )

        with self.subTest("Value matching tests elements"):
            # self.assertFalse(batch_data.accepts("But we want an iterable"))
            self.assertTrue(batch_data.accepts(["don't panic", TestCase()]))
            self.assertFalse(batch_data.accepts(["don't allow None", None]))

            self.assertFalse(batch_none.accepts(None))
            self.assertTrue(batch_none.accepts([None, "None in iterable is ok"]))

        with self.subTest("Only match other batches"):
            self.assertFalse(batch_data.accepts(data))

        with self.subTest("Match subsets but not supersets"):
            class MyString(str):
                pass

            subset = dtypes.Data(valid_classes=MyString, batched=True)
            superset = dtypes.Data(valid_classes=[TestCase, str, int], batched=True)

            self.assertTrue(batch_data.accepts(subset))
            self.assertFalse(batch_data.accepts(superset))

    def test_choice(self):
        d = dtypes.Choice(default="foo", items=["bar", "foo"])
        self.assertTrue(d.accepts("bar"))
        self.assertFalse(d.accepts("not an item"))

    def test_list(self):
        list1 = dtypes.List(valid_classes=self.subset)

        with self.subTest("Test simple values"):
            self.assertTrue(list1.accepts([1, 2, 3.3]))
            self.assertFalse(
                list1.accepts(np.arange(5)),
                msg=f"Numpy number types are not just int and float, so they shouldn't "
                    "pass for {self.subset}."
            )
            self.assertFalse(
                list1.accepts(5), msg="Non-iterables should not be accepted"
            )

        list2 = dtypes.List(valid_classes=list1.valid_classes)
        list3 = dtypes.List(valid_classes=self.superset)
        data1 = dtypes.Data(valid_classes=list1.valid_classes, batched=True)
        data2 = dtypes.Data(valid_classes=list1.valid_classes, batched=False)
        data3 = dtypes.Data(valid_classes=self.superset, batched=True)
        choice = dtypes.Choice(valid_classes=list1.valid_classes)

        with self.subTest("Test dtypes"):
            self.assertTrue(
                list1.accepts(list2),
                msg="Should accept other lists of equivalent or subset classes"
            )
            self.assertFalse(
                list1.accepts(list3),
                msg="Shouldn't accept lists with superset of classes"
            )
            self.assertTrue(
                list1.accepts(data1),
                msg="Should accept batched data with equivalent or subset classes"
            )
            self.assertFalse(
                list1.accepts(data2), msg="Shouldn't accept non-batched data"
            )
            self.assertFalse(
                list1.accepts(data3),
                msg="Shouldn't accept batched data without more specific classes"
            )
            self.assertFalse(
                list1.accepts(choice),
                msg="Shouldn't accept non-List, non-(batched-)Data dtypes"
            )

        list1.batched = True
        with self.subTest("Test batching"):
            self.assertFalse(list1.accepts([1, 2, 3.3]))
            self.assertTrue(list1.accepts([[1], [2], [3.3]]))

            self.assertFalse(
                list1.accepts(list2),
                msg="Shouldn't accept other unbatched lists."
            )
            list2.batched = True
            self.assertTrue(
                list1.accepts(list2),
                msg="Should accept other batched lists of equivalent or subset classes"
            )
            list3.batched = True
            self.assertFalse(
                list1.accepts(list3),
                msg="Still shouldn't accept lists with superset of classes"
            )

        with self.subTest("Test None acceptance"):
            self.assertFalse(list1.accepts([[1], [2, None], [3.3]]))
            list1.allow_none = True
            self.assertTrue(list1.accepts([[1], None, [3.3]]))

            self.assertFalse(list1.accepts([[1], None, [3.3, None]]))
            list1.valid_classes.append(type(None))
            self.assertTrue(list1.accepts([[1], None, [3.3, None]]))

    def test_cross_dtype_matching(self):
        self.assertFalse(
            dtypes.Choice(valid_classes=self.subset).accepts(
                dtypes.Data(valid_classes=self.subset)
            ),
            msg="Even with matching valid classes, dtypes that do not inherit one from "
                "the other should not match."
        )
        self.assertTrue(
            dtypes.Data(valid_classes=[int, np.integer]).accepts(dtypes.Integer())
        )
        self.assertTrue(
            dtypes.Integer().accepts(dtypes.Data(valid_classes=[int, np.integer]))
        )

    def test_none_values(self):
        for D in [
            dtypes.Boolean,
            dtypes.Choice,
            dtypes.Data,
            dtypes.Data,
            dtypes.Float,
            dtypes.Integer,
            dtypes.List,
            dtypes.String
        ]:
            with self.subTest(f"Test None for {D.__name__}"):
                self.assertTrue(D(allow_none=True).accepts(None))
