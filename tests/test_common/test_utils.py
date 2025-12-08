import datetime
import uuid
from decimal import Decimal
from enum import Enum
from unittest.mock import MagicMock

from django.db.models import Model

from common.utils import normalize_value


class TestUtils:
    def test_normalize_value(self):
        """Test normalize_value with various types."""

        # None
        assert normalize_value(None) is None

        # Primitives
        assert normalize_value("str") == "str"
        assert normalize_value(123) == 123
        assert normalize_value(1.23) == 1.23
        assert normalize_value(True) is True

        # UUID
        u = uuid.uuid4()
        assert normalize_value(u) == str(u)

        # Dates
        dt = datetime.datetime(2023, 1, 1, 12, 0, 0)
        assert normalize_value(dt) == dt.isoformat()
        d = datetime.date(2023, 1, 1)
        assert normalize_value(d) == d.isoformat()
        t = datetime.time(12, 0, 0)
        assert normalize_value(t) == t.isoformat()

        # Decimal
        dec = Decimal("10.5")
        assert normalize_value(dec) == 10.5

        # Enum
        class TestEnum(Enum):
            A = "value_a"

        assert normalize_value(TestEnum.A) == "value_a"

        # Model
        mock_model = MagicMock(spec=Model)
        mock_model.pk = 999

        # unittest.mock.MagicMock(spec=Model) returns True for isinstance(obj, Model) check
        # BUT we need to ensure isinstance(value, Model) works in the function.
        # Since we cannot easily instantiate a real Django model without DB, use a class that inherits from Model
        class DummyModel(Model):
            pk = 123

            def __str__(self):
                return "dummy"

            class Meta:
                app_label = "tests"

        assert normalize_value(mock_model) == "999"

        # List/Tuple
        assert normalize_value([1, u]) == [1, str(u)]
        assert normalize_value((1, u)) == [1, str(u)]

        # Dict
        assert normalize_value({"a": 1, "b": u}) == {"a": 1, "b": str(u)}

        # Fallback (object)
        class Unknown:
            def __str__(self):
                return "unknown"

        assert normalize_value(Unknown()) == "unknown"
