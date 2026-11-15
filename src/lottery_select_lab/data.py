"""Loading, validating and producing draw data.

中文：负责把各种格式的历史开奖文件读成统一的 :class:`Draw` 列表，
并提供「合成数据生成器」，让任何人 clone 仓库后无需真实数据就能跑通全部 demo。

Originally the scripts opened a hard-coded Windows path such as
``C:\\Users\\<name>\\Desktop\\彩票研究\\data_3.txt`` and parsed it inline.
中文：原始手稿在每处入口都硬编码了 Windows 路径并就地解析，这里统一收口到本模块。
"""

from __future__ import annotations

import csv
import random
import re
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Union

from .models import RED_POOL_SIZE, REDS_PER_DRAW, Draw

_DELIMITERS = re.compile(r"[,，\t]+")
_NUMBERS = re.compile(r"\d+")


def _parse_reds(field: str) -> tuple[int, ...]:
    """Extract red balls from a free-form field. / 从任意分隔符的字段里提取红球。

    手稿用单空格分隔，但真实数据常混用 ``/`` ``+`` 等符号，这里一律按「提取所有整数」处理。
    """
    numbers = [int(n) for n in _NUMBERS.findall(field)]
    if len(numbers) < REDS_PER_DRAW:
        raise ValueError(f"cannot find {REDS_PER_DRAW} reds in field: {field!r}")
    return tuple(sorted(numbers[:REDS_PER_DRAW]))


def parse_line(line: str) -> Optional[Draw]:
    """Parse one raw text line into a :class:`Draw`, or ``None`` if it is not data.

    中文：解析单行原始文本；表头、空行、注释行返回 ``None``。
    兼容三种布局：``期号,日期,红球,蓝球`` / ``期号,红球,蓝球`` / ``红球,蓝球``。
    """
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None

    fields = [f for f in _DELIMITERS.split(stripped) if f != ""]
    if len(fields) >= 4:
        issue, date, red_field, blue_field = fields[0], fields[1], fields[2], fields[3]
    elif len(fields) == 3:
        issue, date, red_field, blue_field = fields[0], "", fields[1], fields[2]
    elif len(fields) == 2:
        issue, date, red_field, blue_field = "", "", fields[0], fields[1]
    else:
        return None

    # Header rows carry no digits in the red field — skip them silently.
    # 中文：表头的红球字段里没有数字，直接跳过。
    if not _NUMBERS.search(red_field):
        return None

    reds = _parse_reds(red_field)
    blue_digits = _NUMBERS.findall(blue_field)
    blue = int(blue_digits[0]) if blue_digits else None
    return Draw(issue=issue, reds=reds, date=date, blue=blue)


def load_draws(path: Union[str, Path], encoding: str = "utf-8") -> List[Draw]:
    """Load every valid draw from a text/CSV file. / 从文本或 CSV 文件读取全部开奖记录。

    Raises:
        FileNotFoundError: 路径不存在 / path does not exist.
        ValueError: 有效记录少于 2 期 / fewer than two valid draws.
    """
    file_path = Path(path)
    if not file_path.is_file():
        raise FileNotFoundError(f"data file not found: {file_path}")

    draws: List[Draw] = []
    with file_path.open("r", encoding=encoding, errors="replace") as handle:
        for raw in handle:
            try:
                draw = parse_line(raw)
            except ValueError:
                continue
            if draw is not None:
                draws.append(draw)

    if len(draws) < 2:
        raise ValueError(f"need at least 2 valid draws in {file_path}, got {len(draws)}")

    _ensure_chronological(draws, source=file_path)
    return draws


def _ensure_chronological(draws: Sequence[Draw], source: Optional[Path] = None) -> List[Draw]:
    """Warn-only consistency check: issue numbers should increase over time.

    中文：只做提示不做纠正——排序口径一旦被悄悄改掉，回测结果就不可复现了。
    """
    issues = [d.issue for d in draws if d.issue.isdigit() and len(d.issue) >= 6]
    if len(issues) >= 2 and any(int(a) >= int(b) for a, b in zip(issues, issues[1:])):
        import warnings

        warnings.warn(
            f"{source or 'input'} is not sorted by issue; "
            "back-test window semantics assume ascending issue order",
            RuntimeWarning,
            stacklevel=2,
        )
    return list(draws)


def make_synthetic_draws(
    n: int = 300,
    seed: Optional[int] = 42,
    start_issue: int = 2000001,
) -> List[Draw]:
    """Generate reproducible uniform draws. / 生成可复现的均匀随机开奖记录。

    为什么需要：真实开奖数据体积大且不适合进仓库；合成数据的命中率期望是解析可算的，
    等于给所有 demo 内置了一把「标尺」——任何策略都不该显著优于它。

    Args:
        n: 期数 / number of issues.
        seed: 随机种子，``None`` 表示不复现 / seed for reproducibility.
        start_issue: 起始期号 / first issue number.
    """
    rng = random.Random(seed)
    draws: List[Draw] = []
    for offset in range(n):
        reds = tuple(sorted(rng.sample(range(1, RED_POOL_SIZE + 1), REDS_PER_DRAW)))
        blue = rng.randint(1, 16)
        draws.append(Draw(issue=f"{start_issue + offset}", reds=reds, blue=blue))
    return draws


def save_draws(draws: Iterable[Draw], path: Union[str, Path]) -> Path:
    """Write draws back as CSV (same layout the loader understands). / 按加载器可识别的布局写回 CSV。"""
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["issue", "date", "reds", "blue"])
        for draw in draws:
            writer.writerow(draw.to_row())
    return file_path


def split_train_test(draws: Sequence[Draw], warmup: int) -> tuple[List[Draw], List[Draw]]:
    """Split off a warm-up prefix usable as history and a test suffix.

    中文：把序列切成「历史预热段」与「测试段」，预热段只作为窗口素材，不参与命中统计。
    """
    if warmup < 1 or warmup >= len(draws):
        raise ValueError(f"warmup must be in 1..{len(draws) - 1}, got {warmup}")
    return list(draws[:warmup]), list(draws[warmup:])
