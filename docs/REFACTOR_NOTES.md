# Refactor notes / 重构说明

> 对照对象：`legacy/handwritten_v1/` 下的 6 份原始手稿（`test.py` → `test_5.py`）。
> 原始手稿**原样保留**，一是追溯演进，二是方便逐函数核对语义。

## 1. 演进脉络 / Lineage

| 文件 | 主题 | 结论 |
| --- | --- | --- |
| `test.py` | 固定权重参数，跑多窗口回测 | 建立 `平均命中率` 指标 |
| `test_1.py` | 位次命中频次散点图 | 发现「位次」比「得分」更值得研究 |
| `test_2.py` | 手工指定 6 个"优秀因子"位次 `[0,2,7,9,14,32]` | 固定因子不可靠 |
| `test_3.py` | 自动挖掘位次因子 | 有效，但**用了全样本** |
| `test_4.py` | 滚动预测 + 19 次预测共识投票 | 思路正确，代码耦合严重 |
| `test_5.py` | 工程化整理（`data_process` / `weight_h_d` / `inheritance_mix_33` / `start_prediction`） | 主力版本，但仍有死代码 |

## 2. 函数级映射 / Function mapping

| 手稿 | 重构后 | 变化 |
| --- | --- | --- |
| `create_33()` | `weights.zeros33()` | 语义命名 |
| `merge_33(a,b)` | numpy 向量相加 / `weights.weight_matrix` | 一次建矩阵，全局复用 |
| 内联的 `if j==1 / j==33` 权重分支 | `weights.draw_weight_vector()` | 单独成函数 + 单测锁边界 |
| `guess(a,p)` / `map_w()` | `ranking.rank_order()` + `ranking.select_top_k()` | **不再修改入参**；O(n log n) |
| `map_s(weight, subscript)` | `ranking.numbers_at_ranks()` | 显式 0 起位次 + 越界校验 |
| `acc(a,b,i)` | `metrics.hit_count()` | 号码口径，纯函数 |
| `acc_t(a,b,i)` | `ranking.ranks_of()` | 位次口径，两种口径不再混用 |
| `find_w()` | `backtest.RankFactorTracker.rank_factors()` | 增量统计，去掉前视 |
| `find_r()` | `weights.window_scores()` + `ranking.numbers_at_ranks()` | 拆成两个可复用步骤 |
| `inheritance_mix_33()` | `weights.horizon_scores()` | 去掉硬编码 90 |
| `subscripts_mix_6()` | `ranking.vote()` | 票数汇总显式化 |
| `data_process()` | `data.load_draws()` | 支持 csv/txt、多种分隔符、校验 |
| `start_prediction()`（空函数） | `predict.predict_next()` | **补完实现** |
| `main()` 尾部的 `add/hitnum/hitp` | `metrics.summarize()` / `report.*` | 同时输出 CSV/JSON/Markdown |
| `LOG_*.txt` 手工拼接 | `metrics.format_report()` + `report` | 结构化 + 可粘贴进 README |

## 3. 重构中修掉的问题 / Issues fixed

### 3.1 正确性 / Correctness

1. **前视偏差（高）**：`test_3/4/5` 用全样本挖位次因子。已改为默认 `mode="expanding"`，
   `mode="full"` 仅用于对照；`tests` 断言 full 不可能低于 expanding。
2. **破坏性排序（高）**：`guess()` 把入参数组元素改成 `-1`。若调用方复用同一数组，
   第二次调用即得到全错次序。`rank_order()` 改为纯函数。
3. **零值冷启动误判（中）**：`find_w()` 用 `maxi = 0` 找最大值，样本全零时返回位次 0
   并把 `0` 当作有效因子。改为「全零时确定性退化为前 k 位」并显式说明。
4. **循环变量残留（中）**：`acc(guess_res, lst_processed, i+j+1)` 依赖 `for j in range(l)`
   结束后的残留值；一旦循环上界改动就静默错位。已删除。
5. **空蓝球崩溃（低）**：`intlst(a[3])` 遇到空字段抛 `ValueError`。解析器改为蓝球可缺省。

### 3.2 可维护性 / Maintainability

6. **硬编码 Windows 路径（高）**：`C:\Users\29158\Desktop\彩票研究\`。已全部改为参数/CLI 参数。
7. **魔法数字**：`90`（混窗数量）、`19`（回看）、`33`、`6`。已提为常量与配置项。
8. **死代码**：`inheritance_mix_33` / `verify` / `subscripts_mix_6` 在 `test_5` 主线中未被调用；
   `find_w` 的 `p` 参数未使用。已删除或补完（新增 `predict_next` 真正用上它们）。
9. **命名**：`a/b/c/h/d/p/l/r/i/j/k` → 语义化参数与类型注解。
10. **重复代码**：6 份脚本 90% 相同。现为 6 个模块，每个概念只有一处实现。

### 3.3 性能 / Performance

11. **O(n³) 手写排序 + O(N²) 重算**：300 期、19 窗口从分钟级降到 **< 1 秒**。
    `test_incremental_tracker_matches_batch` 保证结果逐位一致。
12. **每期新建 33 长数组做累加**：改为一次性 `(N, 33)` 矩阵 + 向量化滑窗求和。

## 4. 刻意保留的东西 / Deliberately preserved

- **评分语义完全不变**：`hit` / `diffusive` 的加法位置、越界不回绕、同分取小号码，
  全部与手稿一致，并有单测对照「朴素实现」逐值比对。
- **"结论不美化"**：合成数据上所有策略 ≈ 基线。README 直接写出来，不做营销式包装。
- **原始手稿保留在 `legacy/`**：不删、不改，作为演进证据与方法学对照材料。

## 5. 后续 / Roadmap

- v2：把 `band` / `repeat` / `rule1-4` 等因子并入统一评分（等待下一批代码归档）。
- v2：图网络拓扑特征（号码共现图、社区发现）接入 `ranking`。
- v3：超参搜索与滚动可选样本外验证（walk-forward）。
- v3：Notebook 化教学篇：一图看懂「为什么彩票不可预测」。
