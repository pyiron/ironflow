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
            dtypes.Boolean,
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
        batch_data = dtypes.Data(valid_classes=valid_classes, batched=True)
        batch_none = dtypes.Data(
            valid_classes=valid_classes, batched=True, allow_none=True
        )

        with self.subTest("Value matching tests elements"):
            self.assertFalse(batch_data.matches("But we want an iterable"))
            self.assertTrue(batch_data.matches(["don't panic", TestCase()]))
            self.assertFalse(batch_data.matches(["don't allow None", None]))

            self.assertFalse(batch_none.matches(None))
            self.assertTrue(batch_none.matches([None, "None in iterable is ok"]))

        with self.subTest("Only match other batches"):
            self.assertFalse(batch_data.matches(data))

        with self.subTest("Match subsets but not supersets"):
            class MyString(str):
                pass

            subset = dtypes.Data(valid_classes=MyString, batched=True)
            superset = dtypes.Data(valid_classes=[TestCase, str, int], batched=True)

            self.assertTrue(batch_data.matches(subset))
            self.assertFalse(batch_data.matches(superset))

    def test_untyped(self):
        untyped = dtypes.Untyped(default=42)
        self.assertTrue(untyped.matches(7))
        self.assertTrue(untyped.matches(dtypes.Data(valid_classes=object)))
        self.assertFalse(untyped.matches(None))
        self.assertFalse(untyped.matches(dtypes.Integer(allow_none=True)))
        self.assertFalse(untyped.matches(dtypes.Integer(batched=True)))

        untyped.batched = True
        self.assertTrue(untyped.matches([1, 2, 3]))
        self.assertTrue(untyped.matches(dtypes.Integer(batched=True)))
        self.assertFalse(untyped.matches(dtypes.Integer()))
        self.assertFalse(untyped.matches([1, None, 3]))

        untyped.allow_none = True
        self.assertTrue(untyped.matches([1, None, 3]))
