"""Tests for data loading and synthetic generation. / 数据加载与合成数据测试。

中文：手稿假设「文件一定在 C 盘那个路径、一定是 4 列逗号分隔」，
这里验证解析器能吃掉各种脏格式，同时在文件缺失时给出明确报错而不是崩在半路。
"""

from __future__ import annotations

import pytest

from lottery_select_lab.data import (
    load_draws,
    make_synthetic_draws,
    parse_line,
    save_draws,
    split_train_test,
)


def test_parse_four_field_line() -> None:
    draw = parse_line("2024001,2024-01-02,3 8 12 19 25 31,7")
    assert draw is not None
    assert draw.issue == "2024001"
    assert draw.date == "2024-01-02"
    assert draw.reds == (3, 8, 12, 19, 25, 31)
    assert draw.blue == 7


def test_parse_three_field_and_tabbed_lines() -> None:
    assert parse_line("2024002,1 2 3 4 5 6,9").reds == (1, 2, 3, 4, 5, 6)
    assert parse_line("2024003\t7 9 11 13 15 17\t2").blue == 2


def test_parse_header_and_blank_are_skipped() -> None:
    assert parse_line("issue,date,reds,blue") is None
    assert parse_line("   ") is None
    assert parse_line("# comment") is None


def test_parse_sorts_and_validates() -> None:
    draw = parse_line("2024004,,31 25 19 12 8 3,1")
    assert draw.reds == (3, 8, 12, 19, 25, 31)


def test_parse_rejects_duplicates_and_bad_range() -> None:
    with pytest.raises(ValueError):
        parse_line("2024005,,1 1 2 3 4 5,1")
    with pytest.raises(ValueError):
        parse_line("2024006,,1 2 3 4 5 40,1")


def test_roundtrip_save_and_load(tmp_path) -> None:
    draws = make_synthetic_draws(12, seed=5)
    path = save_draws(draws, tmp_path / "sample.csv")
    loaded = load_draws(path)
    assert [d.reds for d in loaded] == [d.reds for d in draws]
    assert [d.issue for d in loaded] == [d.issue for d in draws]


def test_load_missing_file_raises(tmp_path) -> None:
    with pytest.raises(FileNotFoundError):
        load_draws(tmp_path / "nope.csv")


def test_synthetic_is_reproducible_and_valid() -> None:
    a = make_synthetic_draws(50, seed=11)
    b = make_synthetic_draws(50, seed=11)
    assert [d.reds for d in a] == [d.reds for d in b]
    for draw in a:
        assert len(set(draw.reds)) == 6
        assert all(1 <= n <= 33 for n in draw.reds)


def test_split_train_test() -> None:
    draws = make_synthetic_draws(30, seed=8)
    history, test = split_train_test(draws, warmup=10)
    assert len(history) == 10 and len(test) == 20
    assert history[-1].issue == draws[9].issue
    assert test[0].issue == draws[10].issue


def test_split_train_test_rejects_bad_warmup() -> None:
    draws = make_synthetic_draws(10, seed=9)
    with pytest.raises(ValueError):
        split_train_test(draws, warmup=0)
    with pytest.raises(ValueError):
        split_train_test(draws, warmup=10)
