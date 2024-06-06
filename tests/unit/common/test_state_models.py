import pytest

from src.common.state_models import Permission


@pytest.mark.parametrize(
    "first, second, is_lt, is_le, is_gt, is_ge",
    [
        (Permission.EVERYBODY, Permission.EVERYBODY, False, True, False, True),
        (Permission.EVERYBODY, Permission.MODERATOR, True, True, False, False),
        (Permission.EVERYBODY, Permission.BROADCASTER, True, True, False, False),

        (Permission.MODERATOR, Permission.EVERYBODY, False, False, True, True),
        (Permission.MODERATOR, Permission.MODERATOR, False, True, False, True),
        (Permission.MODERATOR, Permission.BROADCASTER, True, True, False, False),

        (Permission.BROADCASTER, Permission.EVERYBODY, False, False, True, True),
        (Permission.BROADCASTER, Permission.MODERATOR, False, False, True, True),
        (Permission.BROADCASTER, Permission.BROADCASTER, False, True, False, True),
    ],
)
def test_permission_comparison(first, second, is_lt, is_le, is_gt, is_ge):
    assert (first < second) == is_lt
    assert (first <= second) == is_le
    assert (first > second) == is_gt
    assert (first >= second) == is_ge
