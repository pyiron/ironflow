# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.

from unittest import TestCase

from ryvencore.utils import deserialize, serialize

from ironflow.model import dtypes


class TestDTypes(TestCase):
    def test_from_string(self):
        self.assertEqual(dtypes.Data, dtypes.DType.from_str("DType.Data"))

    def test_serialization(self):
        default = "foo"
        items = ["bar", default]
        allow_none = True
        valid_classes = str
        choice = dtypes.Choice(
            default=default,
            items=items,
            allow_none=allow_none,
            valid_classes=valid_classes
        )
        reloaded = dtypes.Choice(_load_state=deserialize(serialize(choice.get_state())))
        self.assertEqual(choice.default, reloaded.default)
        self.assertEqual(choice.items, reloaded.items)
        self.assertEqual(choice.allow_none, reloaded.allow_none)
        self.assertEqual(choice.valid_classes, reloaded.valid_classes)

    def test_matching(self):
        with self.subTest("Simple types"):
            d = dtypes.Integer()
            self.assertTrue(d.matches(dtypes.Integer()), msg="DTypes should match")
            self.assertTrue(d.matches(7), msg="Value should match")
            self.assertFalse(d.matches(dtypes.String), msg="DTypes should not match")
            self.assertFalse(d.matches([]), msg="Value should not match")

        classes1 = [int, float]
        classes2 = [int, float, str]
        for D in [dtypes.Choice, dtypes.Data]:
            with self.subTest(
                    f"Test valid classes as subsets for {d.__class__.__name__}"
            ):
                self.assertTrue(
                    D(valid_classes=classes2).matches(D(valid_classes=classes1)),
                    msg="DTypes should match when classes are a subset"
                )
                self.assertFalse(
                    D(valid_classes=classes1).matches(D(valid_classes=classes2)),
                    msg="DTypes should not match when classes are a superset"
                )
            self.assertTrue(
                dtypes.Data(valid_classes=int).matches(7),
                msg="Value should match"
            )
            self.assertFalse(
                dtypes.Data(valid_classes=int).matches("foo"),
                msg="Value should not match"
            )

        with self.subTest("Ensure specificity works only within dtypes"):
            self.assertFalse(
                dtypes.Choice(valid_classes=classes1).matches(
                    dtypes.Data(valid_classes=classes1)
                )
            )

        with self.subTest("Test choices"):
            d = dtypes.Choice(default="foo", items=["bar", "foo"])
            self.assertTrue(d.matches("bar"))
            self.assertFalse(d.matches("not an item"))

        for D in [
            dtypes.BatchedData,
            dtypes.Boolean,
            dtypes.Char,
            dtypes.Choice,
            dtypes.Data,
            dtypes.Data,
            dtypes.Float,
            dtypes.Integer,
            dtypes.List,
            dtypes.String
        ]:
            with self.subTest(f"Test None for {d.__class__.__name__}"):
                self.assertTrue(D(allow_none=True).matches(None))

    def test_batched_data(self):
        valid_classes = [TestCase, str]
        data = dtypes.Data(valid_classes=valid_classes)
        batch_from_dtype = dtypes.BatchedData(batched_dtype=data)
        batch_from_valid_classes = dtypes.BatchedData(valid_classes=valid_classes)

        with self.subTest("Initialization equivalence"):
            self.assertEqual(
                set(batch_from_dtype.valid_classes),
                set(batch_from_valid_classes.valid_classes)
            )

        with self.subTest("Mutual exclusivity"):
            with self.assertRaises(ValueError):
                batch_from_both = dtypes.BatchedData(
                    batched_dtype=data, valid_classes=valid_classes
                )

        with self.subTest("Value matching tests elements"):
            self.assertFalse(batch_from_dtype.matches("Defintely a string"))
            self.assertTrue(batch_from_dtype.matches(["don't panic", TestCase()]))

        with self.subTest("Only match other batches"):
            self.assertFalse(batch_from_dtype.matches(data))

        with self.subTest("Match subsets but not supersets"):
            class MyString(str):
                pass

            subset = dtypes.BatchedData(valid_classes=MyString)
            superset = dtypes.BatchedData(valid_classes=[TestCase, str, int])

            self.assertTrue(batch_from_dtype.matches(subset))
            self.assertFalse(batch_from_dtype.matches(superset))
