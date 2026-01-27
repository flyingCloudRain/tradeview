<template>
  <div class="lhb-hot">
    <el-card class="lhb-card" shadow="never">
      <template #header>
        <span>龙虎榜</span>
      </template>

      <div class="lhb-layout">
        <!-- 内容区域 -->
        <div class="lhb-content">
          <!-- 机构交易统计 - 使用tabs显示3级菜单 -->
          <div v-if="activeMainMenu === 'statistics'" class="content-section">
            <el-tabs v-model="statisticsSubTab" @tab-change="handleStatisticsSubTabChange" class="sub-menu-tabs">
              <el-tab-pane label="统计图" name="chart">
                <div class="filter-bar">
              <div class="filter-group">
                <el-date-picker
                  v-model="statisticsStartDate"
                  type="date"
                  placeholder="开始日期"
                  format="YYYY-MM-DD"
                  value-format="YYYY-MM-DD"
                  @change="handleStatisticsDateRangeChange"
                  class="filter-input"
                />
                <span class="date-separator">至</span>
                <el-date-picker
                  v-model="statisticsEndDate"
                  type="date"
                  placeholder="结束日期"
                  format="YYYY-MM-DD"
                  value-format="YYYY-MM-DD"
                  @change="handleStatisticsDateRangeChange"
                  class="filter-input"
                />
              </div>
              <el-input
                v-model="statisticsStockCode"
                placeholder="股票代码"
                clearable
                class="filter-input-small"
                @clear="handleStatisticsSearch"
              />
              <el-input
                v-model="statisticsStockName"
                placeholder="股票名称（模糊查询）"
                clearable
                class="filter-input"
                @clear="handleStatisticsSearch"
              />
              <div class="filter-inline-group">
                <span class="filter-inline-label">上榜次数：</span>
                <el-input
                  v-model="minAppearCount"
                  placeholder="最小值"
                  clearable
                  class="filter-number-input-small"
                  @input="(val: string) => handleAppearCountInput('min', val)"
                />
                <span class="range-separator">-</span>
                <el-input
                  v-model="maxAppearCount"
                  placeholder="最大值"
                  clearable
                  class="filter-number-input-small"
                  @input="(val: string) => handleAppearCountInput('max', val)"
                />
              </div>
              <div class="filter-inline-group">
                <span class="filter-inline-label">累计净买入（万元）：</span>
                <el-input
                  v-model="minTotalNetBuyAmount"
                  placeholder="最小值"
                  clearable
                  class="filter-number-input-small"
                  @input="(val: string) => handleNetBuyAmountInput('min', val)"
                />
                <span class="range-separator">-</span>
                <el-input
                  v-model="maxTotalNetBuyAmount"
                  placeholder="最大值"
                  clearable
                  class="filter-number-input-small"
                  @input="(val: string) => handleNetBuyAmountInput('max', val)"
                />
              </div>
              <el-button type="primary" @click="handleStatisticsSearch" :loading="statisticsLoading">
                <el-icon><Search /></el-icon>
                查询
              </el-button>
              <el-button @click="handleStatisticsReset">
                <el-icon><Refresh /></el-icon>
                重置
              </el-button>
            </div>

                <!-- 热力图 -->
                <el-card class="heatmap-chart-card" shadow="hover" v-if="heatmapData && heatmapData.length > 0 && statisticsSubTab === 'chart'">
                  <template #header>
                    <div class="chart-header">
                      <span>机构交易热力图（上榜次数最多个股）</span>
                    </div>
                  </template>
                  <v-chart 
                    v-if="heatmapChartOption && Object.keys(heatmapChartOption).length > 0 && statisticsSubTab === 'chart'"
                    class="heatmap-chart" 
                    :option="heatmapChartOption" 
                    autoresize 
                  />
                  <div class="heatmap-legend">
                    <div class="legend-item">
                      <span class="legend-color" style="background: #F56C6C;"></span>
                      <span>大额买入</span>
                    </div>
                    <div class="legend-item">
                      <span class="legend-color" style="background: #FFB3B3;"></span>
                      <span>小额买入</span>
                    </div>
                    <div class="legend-item">
                      <span class="legend-color" style="background: #FFFFFF; border: 1px solid #ddd;"></span>
                      <span>中性</span>
                    </div>
                    <div class="legend-item">
                      <span class="legend-color" style="background: #95D475;"></span>
                      <span>小额卖出</span>
                    </div>
                    <div class="legend-item">
                      <span class="legend-color" style="background: #67C23A;"></span>
                      <span>大额卖出</span>
                    </div>
                  </div>
                </el-card>
                
                <!-- 净买额占比top10折线图 -->
                <el-card class="line-chart-card" shadow="hover" v-if="netBuyRatioLineChartData && netBuyRatioLineChartData.length > 0 && statisticsSubTab === 'chart'">
                  <template #header>
                    <div class="chart-header">
                      <span>净买额占比Top10个股趋势图</span>
                    </div>
                  </template>
                  <v-chart 
                    v-if="netBuyRatioLineChartOption && Object.keys(netBuyRatioLineChartOption).length > 0 && statisticsSubTab === 'chart'"
                    class="line-chart" 
                    :option="netBuyRatioLineChartOption" 
                    autoresize 
                  />
                </el-card>
              </el-tab-pane>

              <el-tab-pane label="明细" name="detail">
            <div class="filter-bar">
              <div class="filter-group">
                <el-date-picker
                  v-model="statisticsStartDate"
                  type="date"
                  placeholder="开始日期"
                  format="YYYY-MM-DD"
                  value-format="YYYY-MM-DD"
                  @change="handleStatisticsDateRangeChange"
                  class="filter-input"
                />
                <span class="date-separator">至</span>
                <el-date-picker
                  v-model="statisticsEndDate"
                  type="date"
                  placeholder="结束日期"
                  format="YYYY-MM-DD"
                  value-format="YYYY-MM-DD"
                  @change="handleStatisticsDateRangeChange"
                  class="filter-input"
                />
              </div>
              <el-input
                v-model="statisticsStockCode"
                placeholder="股票代码"
                clearable
                class="filter-input-small"
                @clear="handleStatisticsSearch"
              />
              <el-input
                v-model="statisticsStockName"
                placeholder="股票名称（模糊查询）"
                clearable
                class="filter-input"
                @clear="handleStatisticsSearch"
              />
              <div class="filter-inline-group">
                <span class="filter-inline-label">上榜次数：</span>
                <el-input
                  v-model="minAppearCount"
                  placeholder="最小值"
                  clearable
                  class="filter-number-input-small"
                  @input="(val: string) => handleAppearCountInput('min', val)"
                />
                <span class="range-separator">-</span>
                <el-input
                  v-model="maxAppearCount"
                  placeholder="最大值"
                  clearable
                  class="filter-number-input-small"
                  @input="(val: string) => handleAppearCountInput('max', val)"
                />
              </div>
              <div class="filter-inline-group">
                <span class="filter-inline-label">累计净买入（万元）：</span>
                <el-input
                  v-model="minTotalNetBuyAmount"
                  placeholder="最小值"
                  clearable
                  class="filter-number-input-small"
                  @input="(val: string) => handleNetBuyAmountInput('min', val)"
                />
                <span class="range-separator">-</span>
                <el-input
                  v-model="maxTotalNetBuyAmount"
                  placeholder="最大值"
                  clearable
                  class="filter-number-input-small"
                  @input="(val: string) => handleNetBuyAmountInput('max', val)"
                />
              </div>
              <el-button type="primary" @click="handleStatisticsSearch" :loading="statisticsLoading">
                <el-icon><Search /></el-icon>
                查询
              </el-button>
              <el-button @click="handleStatisticsReset">
                <el-icon><Refresh /></el-icon>
                重置
              </el-button>
            </div>

            <el-table
              :data="statisticsTableData"
              :loading="statisticsLoading"
              stripe
              border
              empty-text="暂无数据"
              :default-sort="{ prop: 'appear_count', order: 'descending' }"
              @sort-change="handleStatisticsSortChange"
              class="statistics-table"
            >
              <el-table-column prop="stock_code" label="股票代码" width="120" fixed="left" />
              <el-table-column prop="stock_name" label="股票名称" width="100" show-overflow-tooltip />
              <el-table-column prop="appear_count" label="上榜次数" width="100" align="right" sortable="custom">
                <template #default="{ row }">
                  <el-button
                    type="primary"
                    link
                    @click="handleShowDetail(row)"
                    class="appear-count-btn"
                  >
                    <el-tag type="info" size="small" effect="plain">
                      {{ row.appear_count }}
                    </el-tag>
                  </el-button>
                </template>
              </el-table-column>
              <el-table-column prop="total_net_buy_amount" label="累计净买入" width="140" align="right" sortable="custom">
                <template #default="{ row }">
                  <span :class="getAmountClass(row.total_net_buy_amount)">
                    {{ formatAmount(row.total_net_buy_amount) }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="total_buy_amount" label="累计买入" width="140" align="right" sortable="custom">
                <template #default="{ row }">
                  {{ formatAmount(row.total_buy_amount) }}
                </template>
              </el-table-column>
              <el-table-column prop="total_sell_amount" label="累计卖出" width="140" align="right" sortable="custom">
                <template #default="{ row }">
                  {{ formatAmount(row.total_sell_amount) }}
                </template>
              </el-table-column>
              <el-table-column prop="total_market_amount" label="累计成交额" width="140" align="right" sortable="custom">
                <template #default="{ row }">
                  {{ formatAmount(row.total_market_amount) }}
                </template>
              </el-table-column>
              <el-table-column prop="net_buy_ratio" label="净买额占比" width="110" align="right" sortable="custom">
                <template #default="{ row }">
                  {{ formatPercent(row.net_buy_ratio) }}
                </template>
              </el-table-column>
              <el-table-column prop="avg_close_price" label="平均收盘价" width="120" align="right">
                <template #default="{ row }">
                  {{ formatPrice(row.avg_close_price) }}
                </template>
              </el-table-column>
              <el-table-column label="涨跌幅范围" width="140" align="right">
                <template #default="{ row }">
                  <div class="change-percent-range">
                    <span :class="getPercentClass(row.max_change_percent)">
                      {{ formatPercent(row.max_change_percent) }}
                    </span>
                    <span class="range-separator-small">/</span>
                    <span :class="getPercentClass(row.min_change_percent)">
                      {{ formatPercent(row.min_change_percent) }}
                    </span>
                  </div>
                </template>
              </el-table-column>
              <el-table-column prop="avg_turnover_rate" label="平均换手率" width="120" align="right">
                <template #default="{ row }">
                  {{ formatPercent(row.avg_turnover_rate) }}
                </template>
              </el-table-column>
              <el-table-column prop="avg_circulation_market_value" label="平均流通市值" width="140" align="right">
                <template #default="{ row }">
                  {{ formatAmount(row.avg_circulation_market_value) }}
                </template>
              </el-table-column>
            </el-table>

            <div class="pagination-wrapper">
              <el-pagination
                v-model:current-page="statisticsPagination.current"
                v-model:page-size="statisticsPagination.pageSize"
                :total="statisticsPagination.total"
                :page-sizes="[10, 20, 50, 100]"
                layout="total, sizes, prev, pager, next, jumper"
                @size-change="handleStatisticsSizeChange"
                @current-change="handleStatisticsPageChange"
                class="pagination"
              />
            </div>
              </el-tab-pane>
            </el-tabs>
          </div>

          <!-- 活跃营业部 - 使用tabs显示3级菜单 -->
          <div v-if="activeMainMenu === 'activeBranch'" class="content-section">
            <el-tabs v-model="activeBranchSubTab" @tab-change="handleActiveBranchSubTabChange" class="sub-menu-tabs">
              <el-tab-pane label="买入股票统计" name="buyStocks">
              <div class="filter-bar">
                <el-date-picker
                  v-model="buyStocksStatisticsDate"
                  type="date"
                  placeholder="选择日期（不选则显示最新）"
                  format="YYYY-MM-DD"
                  value-format="YYYY-MM-DD"
                  @change="handleBuyStocksStatisticsDateChange"
                  class="filter-input"
                />
                <el-button type="primary" @click="handleBuyStocksStatisticsSearch" :loading="buyStocksStatisticsLoading">
                  <el-icon><Search /></el-icon>
                  查询
                </el-button>
                <el-button @click="handleBuyStocksStatisticsReset">
                  <el-icon><Refresh /></el-icon>
                  重置
                </el-button>
              </div>

              <el-table
                :data="buyStocksStatisticsTableData"
                :loading="buyStocksStatisticsLoading"
                stripe
                border
                empty-text="暂无数据"
                class="buy-stocks-statistics-table"
              >
                <el-table-column type="index" label="排名" width="80" align="center" />
                <el-table-column prop="stock_name" label="股票名称" min-width="150" show-overflow-tooltip />
                <el-table-column prop="appear_count" label="出现次数" width="120" align="right" sortable="custom">
                  <template #default="{ row }">
                    <el-button
                      type="primary"
                      link
                      @click="handleShowBuyStockBranches(row)"
                      class="appear-count-btn"
                      style="padding: 0; height: auto;"
                    >
                      <el-tag 
                        type="primary" 
                        size="small" 
                        effect="dark"
                        style="cursor: pointer;"
                      >
                        {{ row.appear_count }}
                      </el-tag>
                    </el-button>
                  </template>
                </el-table-column>
                <el-table-column prop="buy_branch_count" label="买入营业部数" width="130" align="right" sortable="custom">
                  <template #default="{ row }">
                    <span style="color: #409EFF; font-weight: 500;">{{ row.buy_branch_count || 0 }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="sell_branch_count" label="卖出营业部数" width="130" align="right" sortable="custom">
                  <template #default="{ row }">
                    <span style="color: #67C23A; font-weight: 500;">{{ row.sell_branch_count || 0 }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="net_buy_amount" label="净买入额" width="140" align="right" sortable="custom">
                  <template #default="{ row }">
                    <span :class="getAmountClass(row.net_buy_amount)" style="font-weight: 500;">
                      {{ formatAmount(row.net_buy_amount || 0) }}
                    </span>
                  </template>
                </el-table-column>
                <el-table-column prop="net_sell_amount" label="净卖出额" width="140" align="right" sortable="custom">
                  <template #default="{ row }">
                    <span :class="getAmountClass(-(row.net_sell_amount || 0))" style="font-weight: 500;">
                      {{ formatAmount(row.net_sell_amount || 0) }}
                    </span>
                  </template>
                </el-table-column>
              </el-table>

              <el-pagination
                v-model:current-page="buyStocksStatisticsPagination.current"
                v-model:page-size="buyStocksStatisticsPagination.pageSize"
                :total="buyStocksStatisticsPagination.total"
                :page-sizes="[10, 20, 50, 100]"
                layout="total, sizes, prev, pager, next, jumper"
                @size-change="handleBuyStocksStatisticsSizeChange"
                @current-change="handleBuyStocksStatisticsPageChange"
                style="margin-top: 20px; justify-content: flex-end"
              />
              </el-tab-pane>

              <el-tab-pane label="营业部信息" name="branchInfo">
              <div class="filter-bar">
                <el-date-picker
                  v-model="activeBranchDate"
                  type="date"
                  placeholder="选择日期（不选则显示最新）"
                  format="YYYY-MM-DD"
                  value-format="YYYY-MM-DD"
                  @change="handleActiveBranchDateChange"
                  class="filter-input"
                />
                <el-input
                  v-model="activeBranchName"
                  placeholder="营业部名称（模糊查询）"
                  clearable
                  class="filter-input"
                  @clear="handleActiveBranchSearch"
                />
                <el-input
                  v-model="activeBranchCode"
                  placeholder="营业部代码"
                  clearable
                  class="filter-input-small"
                  @clear="handleActiveBranchSearch"
                />
                <el-input
                  v-model="activeBranchBuyStockName"
                  placeholder="买入股票名称"
                  clearable
                  class="filter-input"
                  @clear="handleActiveBranchSearch"
                />
                <el-button type="primary" @click="handleActiveBranchSearch" :loading="activeBranchLoading">
                  <el-icon><Search /></el-icon>
                  查询
                </el-button>
                <el-button @click="handleActiveBranchReset">
                  <el-icon><Refresh /></el-icon>
                  重置
                </el-button>
              </div>

              <el-table
                :data="activeBranchTableData"
                :loading="activeBranchLoading"
                stripe
                border
                empty-text="暂无数据"
                @sort-change="handleActiveBranchSortChange"
                class="active-branch-table"
              >
                <el-table-column prop="institution_name" label="营业部名称" min-width="250" show-overflow-tooltip />
                <el-table-column prop="institution_code" label="营业部代码" width="120" />
                <el-table-column prop="buy_stock_count" label="买入个股数" width="110" align="right" sortable="custom" />
                <el-table-column prop="sell_stock_count" label="卖出个股数" width="110" align="right" sortable="custom" />
                <el-table-column prop="buy_amount" label="买入总金额" width="140" align="right" sortable="custom">
                  <template #default="{ row }">
                    {{ formatAmount(row.buy_amount) }}
                  </template>
                </el-table-column>
                <el-table-column prop="sell_amount" label="卖出总金额" width="140" align="right" sortable="custom">
                  <template #default="{ row }">
                    {{ formatAmount(row.sell_amount) }}
                  </template>
                </el-table-column>
                <el-table-column prop="net_amount" label="总买卖净额" width="140" align="right" sortable="custom">
                  <template #default="{ row }">
                    <span :class="getAmountClass(row.net_amount)">
                      {{ formatAmount(row.net_amount) }}
                    </span>
                  </template>
                </el-table-column>
                <el-table-column prop="buy_stocks" label="买入股票" min-width="200" show-overflow-tooltip>
                  <template #default="{ row }">
                    <span v-if="row.buy_stocks">{{ row.buy_stocks }}</span>
                    <span v-else class="text-gray">-</span>
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="120" fixed="right">
                  <template #default="{ row }">
                    <el-button
                      type="primary"
                      link
                      size="small"
                      @click="handleViewBranchDetail(row)"
                      :disabled="!row.institution_code"
                    >
                      查看详情
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>

              <el-pagination
                v-model:current-page="activeBranchPagination.current"
                v-model:page-size="activeBranchPagination.pageSize"
                :total="activeBranchPagination.total"
                :page-sizes="[10, 20, 50, 100]"
                layout="total, sizes, prev, pager, next, jumper"
                @size-change="handleActiveBranchSizeChange"
                @current-change="handleActiveBranchPageChange"
                style="margin-top: 20px; justify-content: flex-end"
              />
              </el-tab-pane>
            </el-tabs>
          </div>

          <!-- 上榜个股 -->
          <div v-if="activeMainMenu === 'stocks'" class="content-section">
          <div class="filter-bar" style="margin-bottom: 10px;">
            <el-radio-group v-model="lhbQueryMode" @change="handleLhbQueryModeChange">
              <el-radio-button label="single">单日查询</el-radio-button>
              <el-radio-button label="range">时间跨度统计</el-radio-button>
            </el-radio-group>
          </div>
          
          <!-- 单日查询模式 -->
          <div v-if="lhbQueryMode === 'single'" class="filter-bar">
            <el-date-picker
              v-model="lhbDate"
              type="date"
              placeholder="选择日期"
              format="YYYY-MM-DD"
              value-format="YYYY-MM-DD"
              @change="handleLhbDateChange"
              class="filter-input"
            />
            <el-input
              v-model="lhbStockCode"
              placeholder="股票代码"
              clearable
              class="filter-input-small"
              @clear="handleLhbSearch"
            />
            <el-input
              v-model="lhbStockName"
              placeholder="股票名称（模糊查询）"
              clearable
              class="filter-input"
              @clear="handleLhbSearch"
            />
            <el-button type="primary" @click="handleLhbSearch" :loading="lhbLoading">
              <el-icon><Search /></el-icon>
              查询
            </el-button>
            <el-button @click="handleLhbReset">
              <el-icon><Refresh /></el-icon>
              重置
            </el-button>
          </div>
          
          <!-- 时间跨度统计模式 -->
          <div v-if="lhbQueryMode === 'range'" class="filter-bar">
            <el-date-picker
              v-model="lhbDateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              format="YYYY-MM-DD"
              value-format="YYYY-MM-DD"
              @change="handleLhbDateRangeChange"
              class="filter-input"
            />
            <el-input
              v-model="lhbStockCode"
              placeholder="股票代码"
              clearable
              class="filter-input-small"
              @clear="handleLhbStatisticsSearch"
            />
            <el-input
              v-model="lhbStockName"
              placeholder="股票名称（模糊查询）"
              clearable
              class="filter-input"
              @clear="handleLhbStatisticsSearch"
            />
            <el-button type="primary" @click="handleLhbStatisticsSearch" :loading="lhbStatisticsLoading">
              <el-icon><Search /></el-icon>
              查询
            </el-button>
            <el-button @click="handleLhbStatisticsReset">
              <el-icon><Refresh /></el-icon>
              重置
            </el-button>
          </div>

          <el-table
            :data="lhbTableData"
            :loading="lhbLoading"
            stripe
            border
            empty-text="暂无数据"
            :default-sort="{ prop: 'net_buy_amount', order: 'descending' }"
            @sort-change="handleLhbSortChange"
            class="lhb-table"
          >
            <el-table-column type="expand" width="50">
              <template #default="{ row }">
                <div class="institution-detail">
                  <el-table
                    :data="row.institutions || []"
                    size="small"
                    border
                    :default-sort="{ prop: 'net_buy_amount', order: 'descending' }"
                  >
                    <el-table-column prop="institution_name" label="机构名称" min-width="200" show-overflow-tooltip />
                    <el-table-column label="净流入" width="150" align="right" sortable>
                      <template #default="{ row: inst }">
                        <span :style="{ color: (parseFloat(inst.net_buy_amount) || 0) > 0 ? 'red' : (parseFloat(inst.net_buy_amount) || 0) < 0 ? 'green' : '' }">
                          {{ formatAmount(inst.net_buy_amount) }}
                        </span>
                      </template>
                    </el-table-column>
                    <el-table-column label="买入金额" width="150" align="right">
                      <template #default="{ row: inst }">
                        {{ formatAmount(inst.buy_amount) }}
                      </template>
                    </el-table-column>
                    <el-table-column label="卖出金额" width="150" align="right">
                      <template #default="{ row: inst }">
                        {{ formatAmount(inst.sell_amount) }}
                      </template>
                    </el-table-column>
                  </el-table>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="stock_code" label="股票代码" width="120" />
            <el-table-column prop="stock_name" label="股票名称" width="150" />
            <el-table-column label="涨跌幅(%)" width="120">
              <template #default="{ row }">
                <span :style="{ color: (parseFloat(row.change_percent) || 0) > 0 ? 'red' : 'green' }">
                  {{ formatPercent(row.change_percent) }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="net_buy_amount" label="净买额" width="150" sortable="custom" align="right">
              <template #default="{ row }">
                <span :style="{ color: (parseFloat(row.net_buy_amount) || 0) > 0 ? 'red' : (parseFloat(row.net_buy_amount) || 0) < 0 ? 'green' : '' }">
                  {{ formatAmount(row.net_buy_amount) }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="turnover_rate" label="换手率(%)" width="120" sortable="custom" />
            <el-table-column prop="concept" label="概念" min-width="200">
              <template #default="{ row }">
                <div v-if="getConceptList(row.concept).length > 0" class="concept-tags">
                  <el-tag
                    v-for="(concept, idx) in getConceptList(row.concept)"
                    :key="idx"
                    size="small"
                    style="margin-right: 4px; margin-bottom: 4px"
                  >
                    {{ concept }}
                  </el-tag>
                </div>
                <span v-else style="color: #909399">无</span>
              </template>
            </el-table-column>
            <el-table-column label="交易机构" width="150">
              <template #default="{ row }">
                <span v-if="row.institutions && row.institutions.length > 0">
                  {{ row.institutions.length }} 家机构
                </span>
                <span v-else class="text-gray">暂无</span>
              </template>
            </el-table-column>
          </el-table>

          <el-pagination
            v-if="lhbQueryMode === 'single'"
            v-model:current-page="lhbPagination.current"
            v-model:page-size="lhbPagination.pageSize"
            :total="lhbPagination.total"
            :page-sizes="[10, 20, 50, 100]"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleLhbSizeChange"
            @current-change="handleLhbPageChange"
            class="pagination"
          />
          
          <!-- 时间跨度统计表格 -->
          <el-table
            v-if="lhbQueryMode === 'range'"
            :data="lhbStatisticsTableData"
            :loading="lhbStatisticsLoading"
            stripe
            border
            empty-text="暂无数据"
            :default-sort="{ prop: 'appear_count', order: 'descending' }"
            @sort-change="handleLhbStatisticsSortChange"
            class="lhb-table"
          >
            <el-table-column prop="stock_code" label="股票代码" width="120" sortable="custom" />
            <el-table-column prop="stock_name" label="股票名称" width="150" sortable="custom" />
            <el-table-column prop="appear_count" label="上榜次数" width="120" sortable="custom" align="center">
              <template #default="{ row }">
                <el-tag type="info">{{ row.appear_count }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="total_net_buy_amount" label="净流入总额" width="180" sortable="custom" align="right">
              <template #default="{ row }">
                <span :style="{ color: row.total_net_buy_amount > 0 ? 'red' : row.total_net_buy_amount < 0 ? 'green' : '' }">
                  {{ formatAmount(row.total_net_buy_amount) }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="total_buy_amount" label="买入总额" width="180" align="right">
              <template #default="{ row }">
                {{ formatAmount(row.total_buy_amount) }}
              </template>
            </el-table-column>
            <el-table-column prop="total_sell_amount" label="卖出总额" width="180" align="right">
              <template #default="{ row }">
                {{ formatAmount(row.total_sell_amount) }}
              </template>
            </el-table-column>
            <el-table-column prop="first_date" label="首次上榜" width="120" align="center">
              <template #default="{ row }">
                {{ row.first_date || '-' }}
              </template>
            </el-table-column>
            <el-table-column prop="last_date" label="最后上榜" width="120" align="center">
              <template #default="{ row }">
                {{ row.last_date || '-' }}
              </template>
            </el-table-column>
          </el-table>

          <el-pagination
            v-if="lhbQueryMode === 'range'"
            v-model:current-page="lhbStatisticsPagination.current"
            v-model:page-size="lhbStatisticsPagination.pageSize"
            :total="lhbStatisticsPagination.total"
            :page-sizes="[10, 20, 50, 100]"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleLhbStatisticsSizeChange"
            @current-change="handleLhbStatisticsPageChange"
            class="pagination"
          />
          </div>

          <!-- 上榜个股机构明细 -->
          <div v-if="activeMainMenu === 'detail'" class="content-section">
            <div class="filter-bar">
              <el-date-picker
                v-model="date"
                type="date"
                placeholder="选择日期"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                @change="handleDateChange"
                class="filter-input"
              />
              <el-input
                v-model="stockCode"
                placeholder="股票代码"
                clearable
                class="filter-input-small"
                @clear="handleSearch"
              />
              <el-input
                v-model="stockName"
                placeholder="股票名称（模糊查询）"
                clearable
                class="filter-input"
                @clear="handleSearch"
              />
              <el-select
                v-model="direction"
                placeholder="操作方向"
                clearable
                class="filter-input-small"
                @change="handleSearch"
              >
                <el-option label="买入" value="买入" />
                <el-option label="卖出" value="卖出" />
              </el-select>
              <el-button type="primary" @click="handleSearch" :loading="loading">
                <el-icon><Search /></el-icon>
                查询
              </el-button>
              <el-button @click="handleReset">
                <el-icon><Refresh /></el-icon>
                重置
              </el-button>
            </div>

            <el-table
              :data="tableData"
              :loading="loading"
              stripe
              border
              empty-text="暂无数据"
              @sort-change="handleSortChange"
              class="detail-table"
            >
              <el-table-column prop="date" label="上榜日" width="120" />
              <el-table-column prop="institution_name" label="营业部名称" min-width="220" show-overflow-tooltip />
              <el-table-column prop="stock_code" label="股票代码" width="120" />
              <el-table-column prop="stock_name" label="股票名称" min-width="120" show-overflow-tooltip />
              <el-table-column prop="flag" label="操作方向" width="100" align="center">
                <template #default="{ row }">
                  <el-tag v-if="row.flag === '买入'" type="danger" size="small">买入</el-tag>
                  <el-tag v-else-if="row.flag === '卖出'" type="success" size="small">卖出</el-tag>
                  <span v-else>-</span>
                </template>
              </el-table-column>
              <el-table-column label="金额" width="150" align="right" sortable="custom" :sort-method="sortByAmount">
                <template #default="{ row }">
                  <span v-if="row.flag === '买入' && row.buy_amount" class="amount-positive">
                    {{ formatAmount(row.buy_amount) }}
                  </span>
                  <span v-else-if="row.flag === '卖出' && row.sell_amount" class="amount-negative">
                    {{ formatAmount(row.sell_amount) }}
                  </span>
                  <span v-else>-</span>
                </template>
              </el-table-column>
            </el-table>

            <el-pagination
              v-model:current-page="pagination.current"
              v-model:page-size="pagination.pageSize"
              :total="pagination.total"
              :page-sizes="[10, 20, 50, 100]"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="handleSizeChange"
              @current-change="handlePageChange"
              class="pagination"
            />
          </div>
        </div>
      </div>
    </el-card>

    <!-- 上榜明细抽屉 -->
    <el-drawer
      v-model="detailDialogVisible"
      :title="`${detailStockInfo.stock_name} (${detailStockInfo.stock_code}) - 上榜明细`"
      size="70%"
      :close-on-click-modal="false"
      direction="rtl"
    >
      <el-table
        :data="detailList"
        :loading="detailLoading"
        stripe
        border
        empty-text="暂无数据"
        style="width: 100%"
      >
        <el-table-column prop="date" label="上榜日期" width="120" />
        <el-table-column prop="close_price" label="收盘价" width="100" align="right">
          <template #default="{ row }">
            {{ formatPrice(row.close_price) }}
          </template>
        </el-table-column>
        <el-table-column prop="change_percent" label="涨跌幅" width="100" align="right">
          <template #default="{ row }">
            <span :class="getPercentClass(row.change_percent)">
              {{ formatPercent(row.change_percent) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="institution_net_buy_amount" label="机构买入净额" width="140" align="right">
          <template #default="{ row }">
            <span :class="getAmountClass(row.institution_net_buy_amount)">
              {{ formatAmount(row.institution_net_buy_amount) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="buyer_institution_count" label="买方机构数" width="110" align="right" />
        <el-table-column prop="seller_institution_count" label="卖方机构数" width="110" align="right" />
        <el-table-column prop="institution_buy_amount" label="机构买入总额" width="140" align="right">
          <template #default="{ row }">
            {{ formatAmount(row.institution_buy_amount) }}
          </template>
        </el-table-column>
        <el-table-column prop="institution_sell_amount" label="机构卖出总额" width="140" align="right">
          <template #default="{ row }">
            {{ formatAmount(row.institution_sell_amount) }}
          </template>
        </el-table-column>
        <el-table-column prop="market_total_amount" label="市场总成交额" width="140" align="right">
          <template #default="{ row }">
            {{ formatAmount(row.market_total_amount) }}
          </template>
        </el-table-column>
        <el-table-column prop="net_buy_ratio" label="净买额占比" width="110" align="right">
          <template #default="{ row }">
            {{ formatPercent(row.net_buy_ratio) }}
          </template>
        </el-table-column>
        <el-table-column prop="turnover_rate" label="换手率" width="100" align="right">
          <template #default="{ row }">
            {{ formatPercent(row.turnover_rate) }}
          </template>
        </el-table-column>
        <el-table-column prop="circulation_market_value" label="流通市值" width="120" align="right">
          <template #default="{ row }">
            {{ formatAmount(row.circulation_market_value) }}
          </template>
        </el-table-column>
        <el-table-column prop="reason" label="上榜原因" min-width="200" show-overflow-tooltip />
      </el-table>
      
      <el-pagination
        v-model:current-page="detailPagination.current"
        v-model:page-size="detailPagination.pageSize"
        :total="detailPagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleDetailSizeChange"
        @current-change="handleDetailPageChange"
        style="margin-top: 20px; justify-content: flex-end"
      />
    </el-drawer>

    <!-- 营业部交易详情对话框 -->
    <el-dialog
      v-model="branchDetailDialogVisible"
      :title="`${selectedBranchName || ''} 交易详情`"
      width="90%"
      :close-on-click-modal="false"
    >
      <div class="filter-bar">
        <el-date-picker
          v-model="branchDetailDate"
          type="date"
          placeholder="选择日期（不选则显示所有）"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
          @change="handleBranchDetailDateChange"
          class="filter-input"
        />
        <el-input
          v-model="branchDetailStockCode"
          placeholder="股票代码"
          clearable
          class="filter-input-small"
          @clear="handleBranchDetailSearch"
        />
        <el-input
          v-model="branchDetailStockName"
          placeholder="股票名称（模糊查询）"
          clearable
          class="filter-input"
          @clear="handleBranchDetailSearch"
        />
        <el-button type="primary" @click="handleBranchDetailSearch" :loading="branchDetailLoading">
          <el-icon><Search /></el-icon>
          查询
        </el-button>
        <el-button @click="handleBranchDetailReset">
          <el-icon><Refresh /></el-icon>
          重置
        </el-button>
      </div>

      <el-table
        :data="branchDetailTableData"
        :loading="branchDetailLoading"
        stripe
        border
        empty-text="暂无数据"
        @sort-change="handleBranchDetailSortChange"
        style="margin-top: 20px"
      >
        <el-table-column prop="date" label="交易日期" width="120" sortable="custom" />
        <el-table-column prop="stock_code" label="股票代码" width="100" />
        <el-table-column prop="stock_name" label="股票名称" width="120" />
        <el-table-column prop="change_percent" label="涨跌幅" width="100" align="right" sortable="custom">
          <template #default="{ row }">
            <span :class="getPercentClass(row.change_percent)">
              {{ formatPercent(row.change_percent) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="buy_amount" label="买入金额" width="140" align="right" sortable="custom">
          <template #default="{ row }">
            {{ formatAmount(row.buy_amount) }}
          </template>
        </el-table-column>
        <el-table-column prop="sell_amount" label="卖出金额" width="140" align="right" sortable="custom">
          <template #default="{ row }">
            {{ formatAmount(row.sell_amount) }}
          </template>
        </el-table-column>
        <el-table-column prop="net_amount" label="净额" width="140" align="right" sortable="custom">
          <template #default="{ row }">
            <span :class="getAmountClass(row.net_amount)">
              {{ formatAmount(row.net_amount) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="reason" label="上榜原因" min-width="200" show-overflow-tooltip />
        <el-table-column prop="after_1d" label="1日后" width="100" align="right" sortable="custom">
          <template #default="{ row }">
            <span :class="getPercentClass(row.after_1d)">
              {{ formatPercent(row.after_1d) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="after_5d" label="5日后" width="100" align="right" sortable="custom">
          <template #default="{ row }">
            <span :class="getPercentClass(row.after_5d)">
              {{ formatPercent(row.after_5d) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="after_10d" label="10日后" width="100" align="right" sortable="custom">
          <template #default="{ row }">
            <span :class="getPercentClass(row.after_10d)">
              {{ formatPercent(row.after_10d) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="after_20d" label="20日后" width="100" align="right" sortable="custom">
          <template #default="{ row }">
            <span :class="getPercentClass(row.after_20d)">
              {{ formatPercent(row.after_20d) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="after_30d" label="30日后" width="100" align="right" sortable="custom">
          <template #default="{ row }">
            <span :class="getPercentClass(row.after_30d)">
              {{ formatPercent(row.after_30d) }}
            </span>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="branchDetailPagination.current"
        v-model:page-size="branchDetailPagination.pageSize"
        :total="branchDetailPagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleBranchDetailSizeChange"
        @current-change="handleBranchDetailPageChange"
        style="margin-top: 20px; justify-content: flex-end"
      />
    </el-dialog>

    <!-- 买入股票对应的营业部详情抽屉 -->
    <el-drawer
      v-model="buyStockBranchesDialogVisible"
      :title="`${selectedStockName || ''} - 活跃营业部交易详情`"
      size="85%"
      :close-on-click-modal="false"
      direction="rtl"
    >
      <div class="filter-bar" style="margin-bottom: 20px;">
        <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
          <el-date-picker
            v-model="buyStockBranchesDate"
            type="date"
            placeholder="选择日期（不选则显示所有）"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            @change="handleBuyStockBranchesDateChange"
            class="filter-input"
            clearable
          />
          <el-button type="primary" @click="fetchBuyStockBranchesData" :loading="buyStockBranchesLoading">
            <el-icon><Search /></el-icon>
            查询
          </el-button>
          <el-button @click="handleBuyStockBranchesReset">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
          <div style="margin-left: auto; color: #909399; font-size: 14px;">
            共 {{ buyStockBranchesPagination.total }} 条记录
          </div>
        </div>
      </div>
      
      <!-- 统计信息卡片 -->
      <el-row :gutter="16" style="margin-bottom: 20px;">
        <el-col :span="6">
          <el-card shadow="hover" style="text-align: center;">
            <div style="font-size: 24px; font-weight: bold; color: #409EFF; margin-bottom: 8px;">
              {{ buyStockBranchesStats.buyBranchCount }}
            </div>
            <div style="color: #909399; font-size: 14px;">买入营业部个数</div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover" style="text-align: center;">
            <div style="font-size: 24px; font-weight: bold; color: #67C23A; margin-bottom: 8px;">
              {{ buyStockBranchesStats.sellBranchCount }}
            </div>
            <div style="color: #909399; font-size: 14px;">卖出营业部个数</div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover" style="text-align: center;">
            <div style="font-size: 24px; font-weight: bold; color: #F56C6C; margin-bottom: 8px;">
              {{ formatAmount(buyStockBranchesStats.totalBuyAmount) }}
            </div>
            <div style="color: #909399; font-size: 14px;">买入金额</div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover" style="text-align: center;">
            <div style="font-size: 24px; font-weight: bold; color: #67C23A; margin-bottom: 8px;">
              {{ formatAmount(buyStockBranchesStats.totalSellAmount) }}
            </div>
            <div style="color: #909399; font-size: 14px;">卖出金额</div>
          </el-card>
        </el-col>
      </el-row>
      <el-table
        :data="buyStockBranchesTableData"
        :loading="buyStockBranchesLoading"
        stripe
        border
        empty-text="暂无数据"
        :default-sort="{ prop: 'date', order: 'descending' }"
        @sort-change="handleBuyStockBranchesSortChange"
        style="width: 100%"
        height="calc(100vh - 280px)"
      >
        <el-table-column prop="date" label="交易日期" width="110" sortable="custom" fixed="left" />
        <el-table-column prop="institution_name" label="营业部名称" min-width="200" show-overflow-tooltip fixed="left" />
        <el-table-column prop="institution_code" label="营业部代码" width="110" />
        <el-table-column prop="stock_code" label="股票代码" width="100" />
        <el-table-column prop="stock_name" label="股票名称" width="120" />
        <el-table-column prop="change_percent" label="涨跌幅" width="90" align="right" sortable="custom">
          <template #default="{ row }">
            <span :style="{ color: (row.change_percent || 0) > 0 ? 'red' : 'green', fontWeight: '500' }">
              {{ formatPercent(row.change_percent) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="buy_amount" label="买入金额" width="130" align="right" sortable="custom">
          <template #default="{ row }">
            <span style="color: #f56c6c;">{{ formatAmount(row.buy_amount) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="sell_amount" label="卖出金额" width="130" align="right" sortable="custom">
          <template #default="{ row }">
            <span style="color: #67c23a;">{{ formatAmount(row.sell_amount) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="net_amount" label="净额" width="130" align="right" sortable="custom">
          <template #default="{ row }">
            <span :class="getAmountClass(row.net_amount)" style="fontWeight: '500'">
              {{ formatAmount(row.net_amount) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="reason" label="上榜原因" min-width="180" show-overflow-tooltip />
        <el-table-column prop="after_1d" label="1日后" width="85" align="right">
          <template #default="{ row }">
            <span :style="{ color: (row.after_1d || 0) > 0 ? 'red' : (row.after_1d || 0) < 0 ? 'green' : '#909399' }">
              {{ formatPercent(row.after_1d) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="after_2d" label="2日后" width="85" align="right">
          <template #default="{ row }">
            <span :style="{ color: (row.after_2d || 0) > 0 ? 'red' : (row.after_2d || 0) < 0 ? 'green' : '#909399' }">
              {{ formatPercent(row.after_2d) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="after_3d" label="3日后" width="85" align="right">
          <template #default="{ row }">
            <span :style="{ color: (row.after_3d || 0) > 0 ? 'red' : (row.after_3d || 0) < 0 ? 'green' : '#909399' }">
              {{ formatPercent(row.after_3d) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="after_5d" label="5日后" width="85" align="right">
          <template #default="{ row }">
            <span :style="{ color: (row.after_5d || 0) > 0 ? 'red' : (row.after_5d || 0) < 0 ? 'green' : '#909399' }">
              {{ formatPercent(row.after_5d) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="110" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.institution_code"
              type="primary"
              link
              size="small"
              @click="handleViewBranchDetailFromBuyStock(row)"
            >
              查看详情
            </el-button>
            <span v-else style="color: #909399; font-size: 12px;">无代码</span>
          </template>
        </el-table-column>
      </el-table>
      
      <el-pagination
        v-model:current-page="buyStockBranchesPagination.current"
        v-model:page-size="buyStockBranchesPagination.pageSize"
        :total="buyStockBranchesPagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleBuyStockBranchesSizeChange"
        @current-change="handleBuyStockBranchesPageChange"
        style="margin-top: 20px; justify-content: flex-end"
      />
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { Search, Refresh } from '@element-plus/icons-vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { HeatmapChart, LineChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  VisualMapComponent,
  CalendarComponent,
} from 'echarts/components'
import VChart from 'vue-echarts'
import dayjs from 'dayjs'
import { formatAmount, formatPercent, formatPrice } from '@/utils/format'
import { useLhbHotStore } from '@/stores/lhbHot'
import { useInstitutionTradingStore } from '@/stores/institutionTrading'
import { useLhbStore } from '@/stores/lhb'
import { institutionTradingApi, type InstitutionTradingStatisticsItem } from '@/api/institutionTrading'
import { lhbApi, type ActiveBranchItem, type ActiveBranchDetailItem, type BuyStockStatisticsItem, type LhbStockStatisticsItem } from '@/api/lhb'
import { ElMessage } from 'element-plus'

// 注册 ECharts 组件
use([
  CanvasRenderer,
  HeatmapChart,
  LineChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  VisualMapComponent,
  CalendarComponent,
])

const lhbHotStore = useLhbHotStore()
const institutionTradingStore = useInstitutionTradingStore()
const lhbStore = useLhbStore()

const route = useRoute()

// 主菜单项：statistics, activeBranch, stocks, detail
// 根据路由查询参数设置初始菜单，如果没有查询参数则默认为 statistics
const getInitialMenu = (): string => {
  const menu = route.query.menu as string
  const validMenus = ['statistics', 'activeBranch', 'stocks', 'detail']
  return menu && validMenus.includes(menu) ? menu : 'statistics'
}
const activeMainMenu = ref(getInitialMenu())
// 3级菜单使用tabs显示
const statisticsSubTab = ref('chart') // 机构交易统计的子tab：chart=统计图, detail=明细
const activeBranchSubTab = ref('buyStocks') // 活跃营业部的子tab：buyStocks=买入股票统计, branchInfo=营业部信息

const date = ref(dayjs().format('YYYY-MM-DD'))
const stockCode = ref('')
const stockName = ref('')
const direction = ref<'买入' | '卖出' | ''>('')

// 获取最近N个交易日（排除周末）
const getRecentTradingDays = (count: number): { startDate: string; endDate: string } => {
  const endDate = dayjs()
  let tradingDays: string[] = []
  let currentDate = endDate
  
  // 往前查找，排除周末（周六=6, 周日=0）
  while (tradingDays.length < count) {
    const weekday = currentDate.day()
    // 排除周末
    if (weekday !== 0 && weekday !== 6) {
      tradingDays.push(currentDate.format('YYYY-MM-DD'))
    }
    currentDate = currentDate.subtract(1, 'day')
    
    // 防止无限循环，最多往前查找60天
    if (endDate.diff(currentDate, 'day') > 60) {
      break
    }
  }
  
  if (tradingDays.length === 0) {
    // 如果没有找到交易日，使用默认值
    return {
      startDate: endDate.subtract(count + 2, 'day').format('YYYY-MM-DD'),
      endDate: endDate.format('YYYY-MM-DD')
    }
  }
  
  // 排序，最早的日期作为开始日期
  tradingDays.sort()
  
  return {
    startDate: tradingDays[0],
    endDate: tradingDays[tradingDays.length - 1]
  }
}

// 初始化最近5个交易日
const recentTradingDays = getRecentTradingDays(5)
const statisticsStartDate = ref(recentTradingDays.startDate)
const statisticsEndDate = ref(recentTradingDays.endDate)
const statisticsStockCode = ref('')
const statisticsStockName = ref('')




// 热力图数据（按日期和股票）
const heatmapData = ref<Array<{
  date: string
  stock_code: string
  stock_name: string
  net_buy_amount: number
  buy_amount: number
  sell_amount: number
  appear_count: number
  net_buy_ratio?: number // 净买额占比（从数据库获取）
}>>([])

// 热力图显示选项
const showHeatmapLabels = ref(true) // 是否显示数值标签，默认显示
const heatmapStockLimit = ref(20) // 热力图显示的股票数量限制
const showYAxisStats = ref(false) // 是否在Y轴显示统计信息（上榜次数/净买入）
const yAxisNameLength = ref(10) // Y轴名称显示长度
const selectedHeatmapStocks = ref<string[]>([]) // 保存筛选出的股票列表，确保Y轴显示所有股票

// 净买额占比折线图数据
const netBuyRatioLineChartData = ref<Array<{
  stock_code: string
  stock_name: string
  data: Array<{
    date: string
    net_buy_ratio: number | null
    institution_buy_amount?: number
    institution_sell_amount?: number
    institution_net_buy_amount?: number
    market_total_amount?: number
  }>
}>>([])

// 多条件查询参数
const minAppearCount = ref<string>('')
const maxAppearCount = ref<string>('')
const minTotalNetBuyAmount = ref<string>('')
const maxTotalNetBuyAmount = ref<string>('')

// 明细弹窗相关
const detailDialogVisible = ref(false)
const detailList = ref<InstitutionTradingStatisticsItem[]>([])
const detailLoading = ref(false)
const detailStockInfo = ref<{ stock_code: string; stock_name: string }>({ stock_code: '', stock_name: '' })
const detailPagination = ref({
  current: 1,
  pageSize: 20,
  total: 0,
})

const tableData = computed(() => lhbHotStore.list)
const loading = computed(() => lhbHotStore.loading)
const pagination = computed(() => lhbHotStore.pagination)

const statisticsTableData = computed(() => institutionTradingStore.aggregatedList)
const statisticsLoading = computed(() => institutionTradingStore.aggregatedLoading)
const statisticsPagination = computed(() => institutionTradingStore.aggregatedPagination)

// 龙虎榜相关
const lhbQueryMode = ref<'single' | 'range'>('single')  // 查询模式：single=单日查询, range=时间跨度统计
const lhbDate = ref(dayjs().format('YYYY-MM-DD'))
const lhbDateRange = ref<[string, string] | null>(null)  // 时间跨度
const lhbStockCode = ref('')
const lhbStockName = ref('')
const lhbTableData = computed(() => lhbStore.list)
const lhbLoading = computed(() => lhbStore.loading)
const lhbPagination = computed(() => lhbStore.pagination)

// 时间跨度统计相关
const lhbStatisticsTableData = ref<any[]>([])
const lhbStatisticsLoading = ref(false)
const lhbStatisticsPagination = ref({
  current: 1,
  pageSize: 20,
  total: 0,
})
const lhbStatisticsSortBy = ref<string | undefined>('appear_count')
const lhbStatisticsOrder = ref<'asc' | 'desc'>('desc')

// 活跃营业部相关
const activeBranchDate = ref('')
const activeBranchName = ref('')
const activeBranchCode = ref('')
const activeBranchBuyStockName = ref('')
const activeBranchTableData = ref<ActiveBranchItem[]>([])
const activeBranchLoading = ref(false)
const activeBranchPagination = ref({
  current: 1,
  pageSize: 20,
  total: 0,
})
const activeBranchSortBy = ref<string | undefined>('net_amount')
const activeBranchOrder = ref<'asc' | 'desc'>('desc')

// 营业部交易详情相关
const branchDetailDialogVisible = ref(false)
const selectedBranchCode = ref('')
const selectedBranchName = ref('')
const branchDetailDate = ref('')
const branchDetailStockCode = ref('')
const branchDetailStockName = ref('')
const branchDetailTableData = ref<any[]>([])
const branchDetailLoading = ref(false)
const branchDetailPagination = ref({
  current: 1,
  pageSize: 20,
  total: 0,
})
const branchDetailSortBy = ref<string | undefined>('date')
const branchDetailOrder = ref<'asc' | 'desc'>('desc')

// 买入股票统计相关
const buyStocksStatisticsDate = ref('')
const buyStocksStatisticsTableData = ref<BuyStockStatisticsItem[]>([])
const buyStocksStatisticsLoading = ref(false)
const buyStocksStatisticsPagination = ref({
  current: 1,
  pageSize: 20,
  total: 0,
})

// 买入股票对应的营业部详情对话框相关
const buyStockBranchesDialogVisible = ref(false)
const selectedStockName = ref('')
const buyStockBranchesTableData = ref<ActiveBranchDetailItem[]>([])
const buyStockBranchesLoading = ref(false)
const buyStockBranchesPagination = ref({
  current: 1,
  pageSize: 20,
  total: 0,
})
const buyStockBranchesDate = ref('')
const buyStockBranchesSortBy = ref<string | undefined>('date')
const buyStockBranchesOrder = ref<'asc' | 'desc'>('desc')

// 统计数据
const buyStockBranchesStats = ref({
  buyBranchCount: 0,      // 买入营业部个数
  sellBranchCount: 0,     // 卖出营业部个数
  totalBuyAmount: 0,      // 买入金额
  totalSellAmount: 0,      // 卖出金额
})

const fetchData = async () => {
  try {
    await lhbHotStore.fetchList({
      date: date.value || undefined,
      stock_code: stockCode.value || undefined,
      stock_name: stockName.value || undefined,
      flag: direction.value || undefined,
    })
    if (tableData.value.length === 0 && !loading.value) {
      ElMessage.info(`该日期(${date.value})暂无龙虎榜数据`)
    }
  } catch (e: any) {
    ElMessage.error(e?.message || '获取龙虎榜失败')
  }
}

const handleDateChange = () => {
  lhbHotStore.setFilters({ date: date.value || undefined })
  fetchData()
}

const handleSearch = () => {
  lhbHotStore.setPagination(1, pagination.value.pageSize)
  fetchData()
}

const handleSizeChange = () => {
  fetchData()
}

const handlePageChange = () => {
  fetchData()
}

const handleSortChange = (sort: { prop: string; order: 'ascending' | 'descending' | null }) => {
  let sortBy = sort.order ? sort.prop : undefined
  // 如果按金额排序，需要根据操作方向选择对应的字段
  if (sortBy === 'amount') {
    // 后端需要支持按buy_amount或sell_amount排序，这里先使用buy_amount
    sortBy = 'buy_amount'
  }
  const order = sort.order === 'ascending' ? 'asc' : sort.order === 'descending' ? 'desc' : undefined
  lhbHotStore.setFilters({
    sort_by: sortBy,
    order,
  })
  fetchData()
}

const sortByAmount = (a: any, b: any) => {
  const aAmount = a.flag === '买入' ? (a.buy_amount || 0) : (a.sell_amount || 0)
  const bAmount = b.flag === '买入' ? (b.buy_amount || 0) : (b.sell_amount || 0)
  return aAmount - bAmount
}

// 处理主菜单切换（仅更新菜单状态，数据加载由 watch 处理）
const handleMainMenuChange = (main: string) => {
  activeMainMenu.value = main
  
  // 重置子菜单tab到默认值
  if (main === 'statistics') {
    statisticsSubTab.value = 'chart'
  } else if (main === 'activeBranch') {
    activeBranchSubTab.value = 'buyStocks'
  }
}

// 处理机构交易统计的tab切换
const handleStatisticsSubTabChange = (tabName: string) => {
  statisticsSubTab.value = tabName
  if (tabName === 'chart') {
    // 切换到统计图时，如果数据已存在，加载图表
    if (statisticsTableData.value.length > 0) {
      nextTick(() => {
        setTimeout(() => {
          fetchHeatmapData()
          nextTick(() => {
            fetchNetBuyRatioLineChartData()
          })
        }, 100)
      })
    } else {
      fetchStatisticsData()
    }
  } else if (tabName === 'detail') {
    fetchStatisticsData()
  }
}

// 兼容旧的 tab 切换逻辑（保留以防其他地方调用）
const handleTabChange = (tabName: string) => {
  if (tabName === 'statistics') {
    handleMainMenuChange('statistics')
    fetchStatisticsData()
  } else if (tabName === 'activeBranch') {
    handleMainMenuChange('activeBranch')
    if (activeBranchSubTab.value === 'buyStocks') {
      fetchBuyStocksStatisticsData()
    } else {
      fetchActiveBranchData()
    }
  } else if (tabName === 'stocks') {
    handleMainMenuChange('stocks')
    fetchLhbData()
  } else if (tabName === 'detail') {
    handleMainMenuChange('detail')
    fetchData()
  }
}

// 处理活跃营业部子tab切换（保留兼容）
const handleActiveBranchSubTabChange = (subTabName: string) => {
  if (subTabName === 'buyStocks') {
    activeBranchSubTab.value = 'buyStocks'
    fetchBuyStocksStatisticsData()
  } else if (subTabName === 'branchInfo') {
    activeBranchSubTab.value = 'branchInfo'
    fetchActiveBranchData()
  }
}


// 获取热力图配置
const heatmapChartOption = computed(() => {
  if (!heatmapData.value || heatmapData.value.length === 0) {
    return {}
  }

  // 获取所有唯一的日期和股票代码
  const dates = Array.from(new Set(heatmapData.value.map(item => item.date))).sort()
  // 使用保存的股票列表，确保Y轴显示所有筛选出的股票
  const stockCodes = selectedHeatmapStocks.value.length > 0 
    ? [...selectedHeatmapStocks.value] 
    : Array.from(new Set(heatmapData.value.map(item => item.stock_code))).sort()
  
  // 调试信息：检查股票数量
  const heatmapDataStockCodes = Array.from(new Set(heatmapData.value.map(item => item.stock_code)))
  console.log('[热力图配置] 股票数量检查:', {
    selectedHeatmapStocks数量: selectedHeatmapStocks.value.length,
    heatmapData中股票数量: heatmapDataStockCodes.length,
    stockCodes数量: stockCodes.length,
    selectedHeatmapStocks列表: selectedHeatmapStocks.value,
    heatmapData中股票列表: heatmapDataStockCodes,
    stockCodes列表: stockCodes,
    缺失的股票: selectedHeatmapStocks.value.filter(code => !heatmapDataStockCodes.includes(code)),
  })
  
  // 调试信息：检查天龙集团是否在数据中
  const tianlongInData = heatmapData.value.filter(item => 
    item.stock_code === '300063' || item.stock_name.includes('天龙集团')
  )
  if (tianlongInData.length > 0) {
    console.log('[热力图配置] 天龙集团在heatmapData中:', {
      数据条数: tianlongInData.length,
      股票代码: tianlongInData[0].stock_code,
      股票名称: tianlongInData[0].stock_name,
      是否在stockCodes中: stockCodes.includes('300063'),
      stockCodes列表: stockCodes,
      筛选出的股票数量: selectedHeatmapStocks.value.length,
    })
  } else {
    console.warn('[热力图配置] 天龙集团不在heatmapData中')
  }
  
  console.log('[热力图配置] Y轴股票列表:', {
    股票数量: stockCodes.length,
    股票列表: stockCodes,
  })
  
  // 创建股票代码到名称和统计信息的映射
  const stockNameMap = new Map<string, string>()
  const stockStatsMap = new Map<string, { 
    appearCount: number
    totalNetBuy: number
    totalBuy: number
    totalSell: number
  }>()
  const stockDailyDataMap = new Map<string, Map<string, {
    net_buy_amount: number
    buy_amount: number
    sell_amount: number
    net_buy_ratio?: number // 净买额占比（从数据库获取）
  }>>()
  
  heatmapData.value.forEach(item => {
    stockNameMap.set(item.stock_code, item.stock_name)
    
    // 统计累计数据
    const existing = stockStatsMap.get(item.stock_code)
    if (existing) {
      existing.appearCount += item.appear_count || 0
      existing.totalNetBuy += item.net_buy_amount || 0
      existing.totalBuy += item.buy_amount || 0
      existing.totalSell += item.sell_amount || 0
    } else {
      stockStatsMap.set(item.stock_code, {
        appearCount: item.appear_count || 0,
        totalNetBuy: item.net_buy_amount || 0,
        totalBuy: item.buy_amount || 0,
        totalSell: item.sell_amount || 0,
      })
    }
    
    // 保存每日详细数据
    if (!stockDailyDataMap.has(item.stock_code)) {
      stockDailyDataMap.set(item.stock_code, new Map())
    }
    const dailyMap = stockDailyDataMap.get(item.stock_code)!
    dailyMap.set(item.date, {
      net_buy_amount: item.net_buy_amount,
      buy_amount: item.buy_amount,
      sell_amount: item.sell_amount,
      net_buy_ratio: item.net_buy_ratio, // 保存净买额占比
    })
  })

  // 准备热力图数据：格式为 [日期索引, 股票索引, 净买入金额]
  const heatmapValues: Array<[number, number, number]> = []
  const values = heatmapData.value.map(item => Math.abs(item.net_buy_amount || 0))
  const maxValue = values.length > 0 ? Math.max(...values) : 0
  // 如果maxValue为0，设置一个默认值以确保visualMap显示
  const visualMapMaxValue = maxValue > 0 ? maxValue : 10000 // 默认10000元
  
  // 调试信息：检查visualMap配置
  console.log('[热力图配置] visualMap配置:', {
    maxValue,
    visualMapMaxValue,
    min: -visualMapMaxValue,
    max: visualMapMaxValue,
    数据点数量: heatmapData.value.length,
  })
  
  heatmapData.value.forEach(item => {
    const dateIndex = dates.indexOf(item.date)
    const stockIndex = stockCodes.indexOf(item.stock_code)
    if (dateIndex >= 0 && stockIndex >= 0) {
      heatmapValues.push([dateIndex, stockIndex, item.net_buy_amount || 0])
    }
  })

  // 只显示前N只股票（按上榜次数排序，相同次数按净流入排序）
  // 注意：数据源已经限制为N只股票，这里再次确保只显示N只
  let displayStockCodes = stockCodes
  // 确保displayStockNameMap包含所有displayStockCodes中的股票名称
  let displayStockNameMap = new Map<string, string>()
  stockCodes.forEach(code => {
    const name = stockNameMap.get(code)
    if (name) {
      displayStockNameMap.set(code, name)
    } else {
      // 如果stockNameMap中没有，尝试从heatmapData中查找
      const item = heatmapData.value.find(item => item.stock_code === code)
      if (item) {
        displayStockNameMap.set(code, item.stock_name)
      } else {
        // 如果还是没有，使用股票代码作为名称
        displayStockNameMap.set(code, code)
      }
    }
  })
  let displayHeatmapValues = heatmapValues
  
  // 调试信息：检查天龙集团的名称映射
  if (displayStockCodes.includes('300063')) {
    console.log('[热力图配置] 天龙集团名称映射检查:', {
      是否在displayStockCodes中: displayStockCodes.includes('300063'),
      名称: displayStockNameMap.get('300063'),
      stockNameMap中是否有: stockNameMap.has('300063'),
      stockNameMap中的名称: stockNameMap.get('300063'),
    })
  }
  
  // 调试信息：记录筛选前的状态
  if (stockCodes.length > heatmapStockLimit.value) {
    console.log('[热力图配置] 股票数量超过限制，将进行二次筛选:', {
      当前股票数: stockCodes.length,
      限制数量: heatmapStockLimit.value,
      天龙集团是否在列表中: stockCodes.includes('300063'),
    })
  }
  
  // 如果使用了保存的股票列表，不应该再次筛选
  // 只有在stockCodes数量超过限制且不是从selectedHeatmapStocks获取的情况下才进行二次筛选
  if (stockCodes.length > heatmapStockLimit.value && selectedHeatmapStocks.value.length === 0) {
    // 计算每只股票的上榜次数和总净买入金额
    const stockStats = new Map<string, { appearCount: number; netBuyAmount: number }>()
    heatmapData.value.forEach(item => {
      const code = item.stock_code
      const existing = stockStats.get(code)
      if (existing) {
        existing.appearCount += item.appear_count || 0
        existing.netBuyAmount += item.net_buy_amount || 0
      } else {
        stockStats.set(code, {
          appearCount: item.appear_count || 0,
          netBuyAmount: item.net_buy_amount || 0,
        })
      }
    })
    
    // 按上榜次数排序，相同次数按净流入排序，取前N只
    const sortedStocks = Array.from(stockStats.entries())
      .sort((a, b) => {
        // 先按上榜次数排序（从多到少）
        if (b[1].appearCount !== a[1].appearCount) {
          return b[1].appearCount - a[1].appearCount
        }
        // 相同上榜次数，按净流入排序（从多到少）
        return b[1].netBuyAmount - a[1].netBuyAmount
      })
      .slice(0, heatmapStockLimit.value)
      .map(([code]) => code)
    
    // 如果天龙集团在selectedHeatmapStocks中但不在sortedStocks中，强制包含
    if (selectedHeatmapStocks.value.includes('300063') && !sortedStocks.includes('300063')) {
      sortedStocks.push('300063')
      console.log('[热力图配置] 二次筛选时强制包含天龙集团')
    }
    
    displayStockCodes = sortedStocks
    // 确保displayStockNameMap包含所有sortedStocks中的股票名称
    displayStockNameMap = new Map<string, string>()
    sortedStocks.forEach(code => {
      const name = stockNameMap.get(code)
      if (name) {
        displayStockNameMap.set(code, name)
      } else {
        // 如果stockNameMap中没有，尝试从heatmapData中查找
        const item = heatmapData.value.find(item => item.stock_code === code)
        if (item) {
          displayStockNameMap.set(code, item.stock_name)
        } else {
          // 如果还是没有，使用股票代码作为名称
          displayStockNameMap.set(code, code)
        }
      }
    })
    
    // 调试信息：检查天龙集团的名称映射（二次筛选后）
    if (sortedStocks.includes('300063')) {
      console.log('[热力图配置] 二次筛选后天龙集团名称映射检查:', {
        是否在sortedStocks中: sortedStocks.includes('300063'),
        名称: displayStockNameMap.get('300063'),
        stockNameMap中是否有: stockNameMap.has('300063'),
        stockNameMap中的名称: stockNameMap.get('300063'),
      })
    }
    displayHeatmapValues = heatmapValues.filter(([, stockIndex]) => 
      sortedStocks.includes(stockCodes[stockIndex])
    ).map(([dateIndex, stockIndex, value]) => {
      const newStockIndex = sortedStocks.indexOf(stockCodes[stockIndex])
      return [dateIndex, newStockIndex, value]
    })
    
    // 调试信息：检查天龙集团是否在筛选后的列表中
    const tianlongInDisplay = sortedStocks.includes('300063')
    console.log('[热力图配置] 二次筛选后:', {
      筛选后股票数: sortedStocks.length,
      天龙集团是否在显示列表中: tianlongInDisplay,
      显示列表: sortedStocks,
    })
    if (!tianlongInDisplay && stockCodes.includes('300063')) {
      console.warn('[热力图配置] 警告: 天龙集团在原始数据中，但被二次筛选过滤掉了')
      // 检查天龙集团的上榜次数和净买入
      const tianlongStats = Array.from(stockStats.entries()).find(([code]) => code === '300063')
      if (tianlongStats) {
        console.log('[热力图配置] 天龙集团统计:', tianlongStats[1])
        // 找出被选中的股票中最小的上榜次数
        const minAppearCount = Math.min(...sortedStocks.map(code => {
          const stats = stockStats.get(code)
          return stats?.appearCount || 0
        }))
        console.log('[热力图配置] 被选中股票的最小上榜次数:', minAppearCount)
      }
    }
  }

  return {
    tooltip: {
      position: 'top',
      backgroundColor: 'rgba(50, 50, 50, 0.9)',
      borderColor: '#333',
      borderWidth: 1,
      color: '#fff',
      fontSize: 12,
      formatter: (params: any) => {
        const dateIndex = params.data[0]
        const stockIndex = params.data[1]
        const value = params.data[2]
        const date = dates[dateIndex]
        const stockCode = displayStockCodes[stockIndex]
        const stockName = displayStockNameMap.get(stockCode) || stockCode
        const stats = stockStatsMap.get(stockCode)
        const totalAppearCount = stats?.appearCount || 0
        const totalNetBuy = stats?.totalNetBuy || 0
        const totalBuy = stats?.totalBuy || 0
        const totalSell = stats?.totalSell || 0
        
        // 获取当日详细数据
        const dailyData = stockDailyDataMap.get(stockCode)?.get(date)
        const dailyBuy = dailyData?.buy_amount || 0
        const dailySell = dailyData?.sell_amount || 0
        
        const valueColor = value > 0 ? '#F56C6C' : value < 0 ? '#67C23A' : '#909399'
        return `
          <div style="padding: 8px; line-height: 1.6;">
            <div style="font-weight: bold; font-size: 14px; margin-bottom: 6px; border-bottom: 1px solid rgba(255,255,255,0.2); padding-bottom: 4px;">
              ${stockName} (${stockCode})
            </div>
            <div style="margin-bottom: 4px;"><span style="color: #909399;">日期：</span>${date}</div>
            <div style="margin-bottom: 4px;">
              <span style="color: #909399;">当日净买入：</span>
              <span style="color: ${valueColor}; font-weight: bold;">${formatAmount(value)}</span>
            </div>
            <div style="margin-bottom: 4px;">
              <span style="color: #909399;">当日买入：</span>
              <span style="color: #F56C6C;">${formatAmount(dailyBuy)}</span>
            </div>
            <div style="margin-bottom: 4px;">
              <span style="color: #909399;">当日卖出：</span>
              <span style="color: #67C23A;">${formatAmount(dailySell)}</span>
            </div>
            <div style="margin-top: 6px; padding-top: 6px; border-top: 1px solid rgba(255,255,255,0.2);">
              <div style="margin-bottom: 2px;"><span style="color: #909399;">累计上榜次数：</span>${totalAppearCount}</div>
              <div style="margin-bottom: 2px;">
                <span style="color: #909399;">累计净买入：</span>
                <span style="color: ${totalNetBuy > 0 ? '#F56C6C' : totalNetBuy < 0 ? '#67C23A' : '#909399'}; font-weight: bold;">
                  ${formatAmount(totalNetBuy)}
                </span>
              </div>
              <div style="font-size: 11px; color: #909399;">
                (累计买入: ${formatAmount(totalBuy)} | 累计卖出: ${formatAmount(totalSell)})
              </div>
            </div>
          </div>
        `
      },
    },
    grid: {
      // 确保有足够的高度显示所有股票：每个股票28px，加上一些边距
      height: Math.max(600, displayStockCodes.length * 28 + 50),
      top: 40, // 减少顶部间距
      bottom: 40, // 添加底部间距，确保底部标签不被截断
      left: showYAxisStats.value ? 180 : 150, // 如果显示统计信息，增加左边距
      right: 80, // 增加右边距，为visualMap留出空间
    },
    xAxis: {
      type: 'category',
      data: dates,
      splitArea: {
        show: true,
      },
      axisLabel: {
        rotate: 45,
        fontSize: 11,
        // 智能显示日期：如果日期数量少于等于20个，显示所有；否则动态调整间隔
        interval: dates.length <= 20 ? 0 : (index: number) => {
          // 如果日期超过20个，计算合适的显示间隔，确保显示约15-20个日期标签
          const step = Math.ceil(dates.length / 18)
          return index % step !== 0
        },
        formatter: (value: string) => {
          // 格式化日期显示：YYYY-MM-DD -> MM/DD 格式，更易读
          if (value && value.length >= 10) {
            const month = value.substring(5, 7)
            const day = value.substring(8, 10)
            return `${month}/${day}`
          }
          return value
        },
      },
    },
    yAxis: {
      type: 'category',
      data: (() => {
        const yAxisData = displayStockCodes.map(code => {
          const name = displayStockNameMap.get(code) || code
          // 调试信息：检查天龙集团是否在Y轴数据中
          if (code === '300063') {
            console.log('[热力图配置] 天龙集团在Y轴数据中:', { 
              code, 
              name,
              displayStockCodes长度: displayStockCodes.length,
              索引: displayStockCodes.indexOf(code),
              displayStockNameMap中是否有: displayStockNameMap.has(code),
            })
          }
          // 使用配置的名称长度限制
          return name.length > yAxisNameLength.value ? name.substring(0, yAxisNameLength.value) + '...' : name
        })
        
        // 调试信息：输出Y轴数据统计
        console.log('[热力图配置] Y轴数据统计:', {
          股票数量: displayStockCodes.length,
          Y轴数据长度: yAxisData.length,
          天龙集团是否在displayStockCodes中: displayStockCodes.includes('300063'),
          天龙集团索引: displayStockCodes.indexOf('300063'),
          Y轴数据前5个: yAxisData.slice(0, 5),
        })
        
        return yAxisData
      })(),
      splitArea: {
        show: true,
        areaStyle: {
          color: ['rgba(250, 250, 250, 0.3)', 'rgba(200, 200, 200, 0.1)'],
        },
      },
      axisLabel: {
        show: true, // 确保显示所有标签
        interval: 0, // 显示所有标签，不跳过任何标签
        formatter: (value: string, index: number) => {
          // 确保index在有效范围内
          if (index < 0 || index >= displayStockCodes.length) {
            console.warn('[热力图配置] Y轴标签索引超出范围:', { index, displayStockCodes长度: displayStockCodes.length })
            return value
          }
          
          const code = displayStockCodes[index]
          const name = displayStockNameMap.get(code) || code
          const stats = stockStatsMap.get(code)
          
          // 智能截断名称，优先保留完整的中文字符
          let shortName = name
          if (name.length > yAxisNameLength.value) {
            // 尝试在合适的位置截断（避免截断中文字符）
            let cutPos = yAxisNameLength.value
            // 如果截断位置是中文的中间，向前调整
            if (name.charCodeAt(cutPos) >= 0xD800 && name.charCodeAt(cutPos) < 0xE000) {
              cutPos--
            }
            shortName = name.substring(0, cutPos) + '...'
          }
          
          // 构建标签文本（只显示股票名称，不显示股票代码）
          let labelText = `{name|${shortName}}`
          
          // 如果启用统计信息显示，添加上榜次数和净买入
          if (showYAxisStats.value && stats) {
            const appearCount = stats.appearCount || 0
            const totalNetBuy = stats.totalNetBuy || 0
            const netBuyText = formatAmount(totalNetBuy)
            // 根据净买入金额设置颜色样式（买入=红色，卖出=绿色）
            const netBuyStyle = totalNetBuy > 0 ? 'netbuy-positive' : totalNetBuy < 0 ? 'netbuy-negative' : 'netbuy-neutral'
            labelText += `\n{stats|上榜:${appearCount}次}`
            labelText += `\n{${netBuyStyle}|${netBuyText}}`
          }
          
          return labelText
        },
        fontSize: 10, // 稍微减小字体，节省空间
        lineHeight: showYAxisStats.value ? 12 : 16, // 减小行高，让标签更紧凑
        rich: {
          name: {
            color: '#303133',
            fontSize: 11, // 稍微减小字体
            fontWeight: 'bold',
            padding: [0, 0, 0, 0],
          },
          stats: {
            color: '#909399',
            fontSize: 9,
            padding: [2, 0, 0, 0],
          },
          'netbuy-positive': {
            color: '#F56C6C',
            fontSize: 9,
            fontWeight: 'bold',
            padding: [1, 0, 0, 0],
          },
          'netbuy-negative': {
            color: '#67C23A',
            fontSize: 9,
            fontWeight: 'bold',
            padding: [1, 0, 0, 0],
          },
          'netbuy-neutral': {
            color: '#909399',
            fontSize: 9,
            fontWeight: 'normal',
            padding: [1, 0, 0, 0],
          },
        },
        width: showYAxisStats.value ? 100 : 80, // 如果显示统计信息，增加宽度
        overflow: 'truncate', // 超出部分截断
      },
    },
    visualMap: {
      show: true, // 确保显示visualMap
      min: -visualMapMaxValue,
      max: visualMapMaxValue,
      calculable: true,
      orient: 'vertical',
      left: 'right',
      top: 'center',
      itemWidth: 15,
      itemHeight: 150,
      inRange: {
        // 使用更直观的颜色方案：红色(大额买入) -> 浅红(小额买入) -> 白色(中性) -> 浅绿(小额卖出) -> 绿色(大额卖出)
        color: ['#67C23A', '#95D475', '#FFFFFF', '#FFB3B3', '#F56C6C'],
      },
      text: ['大额买入', '大额卖出'],
      color: '#303133',
      fontSize: 12,
      formatter: (value: number) => {
        return formatAmount(value)
      },
      // 确保文本显示
      textGap: 10,
      precision: 0, // 整数显示
    },
    series: [
      {
        name: '机构净买入',
        type: 'heatmap',
        data: displayHeatmapValues,
        label: {
          show: showHeatmapLabels.value,
          fontSize: 9, // 稍微减小字体，因为要显示更多信息
          color: '#303133',
          formatter: (params: any) => {
            const dateIndex = params.data[0]
            const stockIndex = params.data[1]
            const value = params.data[2] // 净买额
            
            // 获取当日详细数据
            const date = dates[dateIndex]
            const stockCode = displayStockCodes[stockIndex]
            const dailyData = stockDailyDataMap.get(stockCode)?.get(date)
            
            // 优先使用数据库中的净买额占比
            if (dailyData && dailyData.net_buy_ratio !== undefined && dailyData.net_buy_ratio !== null) {
              // 使用数据库中的净买额占比
              return `${formatAmount(value)} ${formatPercent(dailyData.net_buy_ratio)}`
            }
            
            // 如果没有数据库占比，只显示净买额
            return formatAmount(value)
          },
        },
        itemStyle: {
          borderColor: '#fff',
          borderWidth: 1,
        },
          emphasis: {
            itemStyle: {
              shadowBlur: 15,
              shadowColor: 'rgba(0, 0, 0, 0.6)',
              borderWidth: 2,
              borderColor: '#F56C6C',
            },
          label: {
            show: true,
            fontSize: 11,
            fontWeight: 'bold',
          },
        },
      },
    ],
  }
})

// 净买额占比折线图配置
const netBuyRatioLineChartOption = computed(() => {
  if (!netBuyRatioLineChartData.value || netBuyRatioLineChartData.value.length === 0) {
    return {}
  }

  // 获取所有日期
  const allDates = new Set<string>()
  netBuyRatioLineChartData.value.forEach(stock => {
    stock.data.forEach(item => {
      allDates.add(item.date)
    })
  })
  const dates = Array.from(allDates).sort()

  // 生成10种不同的颜色
  const colors = [
    '#5470C6', '#91CC75', '#FAC858', '#EE6666', '#73C0DE',
    '#3BA272', '#FC8452', '#9A60B4', '#EA7CCC', '#FF9F7F'
  ]

  // 保存详细数据映射，用于tooltip（按股票代码和日期）
  const detailDataMap = new Map<string, Map<string, {
    institution_buy_amount?: number
    institution_sell_amount?: number
    institution_net_buy_amount?: number
    market_total_amount?: number
  }>>()
  
  // 构建series数据（包含详细数据用于tooltip）
  const series = netBuyRatioLineChartData.value.map((stock, index) => {
    const data = dates.map(date => {
      const item = stock.data.find(d => d.date === date)
      return item?.net_buy_ratio !== null && item?.net_buy_ratio !== undefined 
        ? item.net_buy_ratio 
        : null
    })

    // 保存详细数据映射
    const stockDetailMap = new Map<string, {
      institution_buy_amount?: number
      institution_sell_amount?: number
      institution_net_buy_amount?: number
      market_total_amount?: number
    }>()
    stock.data.forEach(item => {
      stockDetailMap.set(item.date, {
        institution_buy_amount: item.institution_buy_amount,
        institution_sell_amount: item.institution_sell_amount,
        institution_net_buy_amount: item.institution_net_buy_amount,
        market_total_amount: item.market_total_amount,
      })
    })
    detailDataMap.set(stock.stock_code, stockDetailMap)

    return {
      name: `${stock.stock_name}(${stock.stock_code})`,
      type: 'line',
      data: data,
      smooth: true,
      symbol: 'circle',
      symbolSize: 6,
      lineStyle: {
        width: 2,
      },
      itemStyle: {
        color: colors[index % colors.length],
      },
      connectNulls: false, // 不连接空值
      label: {
        show: true, // 显示数据点标签
        position: 'top',
        formatter: (params: any) => {
          // 只在有数据时显示标签
          if (params.value !== null && params.value !== undefined) {
            // 显示股票名称和净买额占比（分行显示）
            return `${stock.stock_name}\n${formatPercent(params.value)}`
          }
          return ''
        },
        fontSize: 9,
        color: colors[index % colors.length],
        distance: 10, // 标签距离数据点的距离
        padding: [2, 4, 2, 4], // 标签内边距
        backgroundColor: 'rgba(255, 255, 255, 0.8)', // 白色半透明背景，提高可读性
        borderColor: colors[index % colors.length],
        borderWidth: 1,
        borderRadius: 3,
        fontSize: 9,
        lineHeight: 12,
      },
    }
  })

  return {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(50, 50, 50, 0.9)',
      borderColor: '#333',
      borderWidth: 1,
      color: '#fff',
      fontSize: 12,
      axisPointer: {
        type: 'cross',
        label: {
          backgroundColor: '#6a7985',
        },
      },
      formatter: (params: any) => {
        if (!params || params.length === 0) return ''
        const date = params[0].axisValue
        let result = `<div style="padding: 10px; line-height: 1.8; max-width: 400px;">
          <div style="font-weight: bold; font-size: 15px; margin-bottom: 8px; border-bottom: 1px solid rgba(255,255,255,0.3); padding-bottom: 6px;">
            📅 ${date}
          </div>`
        
        params.forEach((param: any) => {
          if (param.value !== null && param.value !== undefined) {
            const value = param.value
            const color = param.color
            const seriesIndex = param.seriesIndex
            // 从series名称中提取股票代码
            const seriesName = param.seriesName || ''
            const stockCodeMatch = seriesName.match(/\(([^)]+)\)/)
            const stockCode = stockCodeMatch ? stockCodeMatch[1] : ''
            const detailData = stockCode ? detailDataMap.get(stockCode)?.get(date) : undefined
            
            result += `
            <div style="margin-bottom: 8px; padding: 6px; background-color: rgba(255,255,255,0.05); border-radius: 4px;">
              <div style="margin-bottom: 4px;">
                <span style="display: inline-block; width: 12px; height: 12px; background-color: ${color}; border-radius: 50%; margin-right: 8px; vertical-align: middle;"></span>
                <span style="color: #fff; font-weight: bold; font-size: 13px;">${param.seriesName}</span>
              </div>
              <div style="margin-left: 20px; margin-top: 4px;">
                <div style="margin-bottom: 3px;">
                  <span style="color: #909399; font-size: 12px;">净买额占比:</span>
                  <span style="color: ${value > 0 ? '#F56C6C' : value < 0 ? '#67C23A' : '#909399'}; font-weight: bold; margin-left: 6px; font-size: 13px;">
                    ${formatPercent(value)}
                  </span>
                </div>`
            
            // 显示详细信息
            if (detailData) {
              if (detailData.institution_net_buy_amount !== undefined && detailData.institution_net_buy_amount !== null) {
                const netBuyColor = detailData.institution_net_buy_amount > 0 ? '#F56C6C' : detailData.institution_net_buy_amount < 0 ? '#67C23A' : '#909399'
                result += `
                <div style="margin-bottom: 3px;">
                  <span style="color: #909399; font-size: 12px;">净买入:</span>
                  <span style="color: ${netBuyColor}; font-weight: bold; margin-left: 6px; font-size: 12px;">
                    ${formatAmount(detailData.institution_net_buy_amount)}
                  </span>
                </div>`
              }
              if (detailData.institution_buy_amount !== undefined && detailData.institution_buy_amount !== null) {
                result += `
                <div style="margin-bottom: 3px;">
                  <span style="color: #909399; font-size: 12px;">买入:</span>
                  <span style="color: #F56C6C; margin-left: 6px; font-size: 12px;">
                    ${formatAmount(detailData.institution_buy_amount)}
                  </span>
                </div>`
              }
              if (detailData.institution_sell_amount !== undefined && detailData.institution_sell_amount !== null) {
                result += `
                <div style="margin-bottom: 3px;">
                  <span style="color: #909399; font-size: 12px;">卖出:</span>
                  <span style="color: #67C23A; margin-left: 6px; font-size: 12px;">
                    ${formatAmount(detailData.institution_sell_amount)}
                  </span>
                </div>`
              }
              if (detailData.market_total_amount !== undefined && detailData.market_total_amount !== null) {
                result += `
                <div style="margin-bottom: 3px;">
                  <span style="color: #909399; font-size: 12px;">市场总成交:</span>
                  <span style="color: #909399; margin-left: 6px; font-size: 12px;">
                    ${formatAmount(detailData.market_total_amount)}
                  </span>
                </div>`
              }
            }
            
            result += `</div></div>`
          }
        })
        
        result += '</div>'
        return result
      },
    },
    legend: {
      data: netBuyRatioLineChartData.value.map(stock => `${stock.stock_name}(${stock.stock_code})`),
      type: 'scroll',
      orient: 'horizontal',
      bottom: 0,
      fontSize: 11,
      itemWidth: 14,
      itemHeight: 10,
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      top: '10%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: dates,
      axisLabel: {
        rotate: 45,
        fontSize: 11,
        formatter: (value: string) => {
          // 格式化日期显示：YYYY-MM-DD -> MM/DD 格式
          if (value && value.length >= 10) {
            const month = value.substring(5, 7)
            const day = value.substring(8, 10)
            return `${month}/${day}`
          }
          return value
        },
      },
    },
    yAxis: {
      type: 'value',
      name: '净买额占比(%)',
      nameTextStyle: {
        fontSize: 12,
      },
      axisLabel: {
        formatter: (value: number) => {
          return formatPercent(value)
        },
        fontSize: 11,
      },
      splitLine: {
        show: true,
        lineStyle: {
          type: 'dashed',
          color: '#E4E7ED',
        },
      },
    },
    series: series,
  }
})

// 获取趋势方向
const getTrendDirection = (current: number | undefined, prev: number | undefined): 'up' | 'down' | 'same' => {
  if (current === undefined || prev === undefined || prev === 0) return 'same'
  if (current > prev) return 'up'
  if (current < prev) return 'down'
  return 'same'
}

// 获取趋势百分比
const getTrendPercent = (current: number | undefined, prev: number | undefined): string => {
  if (current === undefined || prev === undefined || prev === 0) return '-'
  const change = ((current - prev) / Math.abs(prev)) * 100
  return `${change > 0 ? '+' : ''}${change.toFixed(2)}%`
}

// 获取趋势样式类
const getTrendClass = (current: number | undefined, prev: number | undefined): string => {
  const direction = getTrendDirection(current, prev)
  if (direction === 'up') return 'trend-up'
  if (direction === 'down') return 'trend-down'
  return 'trend-same'
}

// 获取单日所有数据（处理分页）
const fetchAllListData = async (date: string) => {
  const allItems: any[] = []
  let page = 1
  const pageSize = 100 // 使用最大允许的page_size
  let hasMore = true

  while (hasMore) {
    try {
      const res = await institutionTradingApi.getList({
        start_date: date,
        end_date: date,
        page,
        page_size: pageSize,
      })
      
      allItems.push(...res.items)
      
      // 如果返回的数据少于pageSize，说明已经是最后一页
      if (res.items.length < pageSize || page >= res.total_pages) {
        hasMore = false
      } else {
        page++
      }
    } catch (e) {
      console.error(`获取${date}第${page}页数据失败`, e)
      hasMore = false
    }
  }

  return allItems
}

// 获取热力图数据（按日期和股票，只显示上榜次数最多的20个个股）
const fetchHeatmapData = async () => {
  if (!statisticsStartDate.value || !statisticsEndDate.value) {
    heatmapData.value = []
    return
  }

  try {
    const startDate = dayjs(statisticsStartDate.value)
    const endDate = dayjs(statisticsEndDate.value)
    const days = endDate.diff(startDate, 'day') + 1

    // 如果天数太多，不显示热力图
    if (days > 30) {
      heatmapData.value = []
      return
    }

    const heatmapPromises = []
    for (let i = 0; i < days; i++) {
      const date = startDate.add(i, 'day').format('YYYY-MM-DD')
      heatmapPromises.push(fetchAllListData(date))
    }

    const results = await Promise.all(heatmapPromises)
    
    // 统计每只股票的上榜次数
    const stockAppearCountMap = new Map<string, number>()
    results.forEach((items) => {
      items.forEach((item) => {
        const code = item.stock_code
        stockAppearCountMap.set(code, (stockAppearCountMap.get(code) || 0) + 1)
      })
    })
    
    // 找出上榜次数最多的N只股票（可配置）
    const sortedStockEntries = Array.from(stockAppearCountMap.entries())
      .sort((a, b) => b[1] - a[1]) // 按上榜次数倒序
    
    // 检查天龙集团的上榜次数和排名
    const tianlongEntry = sortedStockEntries.find(([code]) => code === '300063')
    if (tianlongEntry) {
      const tianlongRank = sortedStockEntries.findIndex(([code]) => code === '300063') + 1
      console.log('[热力图] 天龙集团上榜统计:', {
        股票代码: tianlongEntry[0],
        上榜次数: tianlongEntry[1],
        排名: tianlongRank,
        是否在前N只: tianlongRank <= heatmapStockLimit.value,
        限制数量: heatmapStockLimit.value,
      })
    } else {
      console.warn('[热力图] 天龙集团未在数据中找到')
    }
    
    const topNStocks = sortedStockEntries
      .slice(0, heatmapStockLimit.value)
      .map(([code]) => code)
    
    // 如果用户明确查询了某只股票（通过股票代码或名称），强制包含在显示列表中
    const forcedStocks: string[] = []
    
    // 如果天龙集团在数据中但不在前N只，强制包含（用于调试）
    if (tianlongEntry && !topNStocks.includes('300063')) {
      forcedStocks.push('300063')
      console.log('[热力图] 强制包含天龙集团（用于调试）')
    }
    if (statisticsStockCode.value && statisticsStockCode.value.trim()) {
      const code = statisticsStockCode.value.trim()
      if (stockAppearCountMap.has(code) && !topNStocks.includes(code)) {
        forcedStocks.push(code)
        console.log('[热力图] 强制包含用户查询的股票代码:', code)
      }
    }
    if (statisticsStockName.value && statisticsStockName.value.trim()) {
      // 查找名称匹配的股票代码
      results.forEach((items) => {
        items.forEach((item) => {
          if (item.stock_name && item.stock_name.includes(statisticsStockName.value.trim())) {
            const code = item.stock_code
            if (stockAppearCountMap.has(code) && !topNStocks.includes(code) && !forcedStocks.includes(code)) {
              forcedStocks.push(code)
              console.log('[热力图] 强制包含用户查询的股票名称:', item.stock_name, code)
            }
          }
        })
      })
    }
    
    // 合并强制包含的股票和排名前N的股票
    const finalStocks = [...topNStocks]
    forcedStocks.forEach(code => {
      if (!finalStocks.includes(code)) {
        finalStocks.push(code)
      }
    })
    
    const topNStocksSet = new Set(finalStocks)
    
    // 保存最终筛选出的股票列表，用于Y轴显示
    selectedHeatmapStocks.value = finalStocks
    console.log('[热力图] 保存筛选出的股票列表:', {
      股票数量: finalStocks.length,
      股票列表: finalStocks,
    })
    
    // 获取所有股票的股票名称映射（从原始数据中）
    const stockNameMap = new Map<string, string>()
    results.forEach((items) => {
      items.forEach((item) => {
        if (topNStocksSet.has(item.stock_code) && !stockNameMap.has(item.stock_code)) {
          stockNameMap.set(item.stock_code, item.stock_name || item.stock_code)
        }
      })
    })
    
    // 确保所有finalStocks中的股票都有名称映射
    finalStocks.forEach(code => {
      if (!stockNameMap.has(code)) {
        // 如果原始数据中没有，尝试从results中查找
        let found = false
        for (const items of results) {
          for (const item of items) {
            if (item.stock_code === code) {
              stockNameMap.set(code, item.stock_name || code)
              found = true
              break
            }
          }
          if (found) break
        }
        // 如果还是没有找到，使用股票代码作为名称
        if (!found) {
          stockNameMap.set(code, code)
        }
      }
    })
    
    // 调试信息：检查股票数量
    console.log('[热力图] 股票数量检查:', {
      topNStocks数量: topNStocks.length,
      forcedStocks数量: forcedStocks.length,
      finalStocks数量: finalStocks.length,
      stockNameMap数量: stockNameMap.size,
      finalStocks列表: finalStocks,
    })
    
    // 更新调试信息
    if (forcedStocks.length > 0) {
      console.log('[热力图] 强制包含的股票:', forcedStocks)
      console.log('[热力图] 最终显示的股票列表:', finalStocks)
    }
    
    // 调试信息：输出上榜次数统计
    console.log('[热力图] 股票上榜次数统计:', Array.from(stockAppearCountMap.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 30)
      .map(([code, count]) => ({ code, count })))
    console.log('[热力图] 将显示的股票:', topNStocks)
    
    const heatmapItems: Array<{
      date: string
      stock_code: string
      stock_name: string
      net_buy_amount: number
      buy_amount: number
      sell_amount: number
      appear_count: number
    }> = []

    // 获取所有有数据的日期
    const datesWithData: string[] = []
    results.forEach((items, index) => {
      const date = startDate.add(index, 'day').format('YYYY-MM-DD')
      if (items && items.length > 0) {
        datesWithData.push(date)
      }
    })

    results.forEach((items, index) => {
      const date = startDate.add(index, 'day').format('YYYY-MM-DD')
      
      // 跳过非交易日：如果没有数据，直接跳过
      if (!items || items.length === 0) {
        return
      }
      
      // 按股票代码聚合当天的数据（只处理上榜次数最多的20只股票）
      const stockMap = new Map<string, {
        stock_code: string
        stock_name: string
        net_buy_amount: number
        buy_amount: number
        sell_amount: number
        appear_count: number
        net_buy_ratio?: number // 净买额占比（从数据库获取）
      }>()

      items.forEach((item) => {
        // 只处理上榜次数最多的N只股票
        if (!topNStocksSet.has(item.stock_code)) {
          return
        }
        
        const code = item.stock_code
        const existing = stockMap.get(code)
        if (existing) {
          existing.net_buy_amount += item.institution_net_buy_amount || 0
          existing.buy_amount += item.institution_buy_amount || 0
          existing.sell_amount += item.institution_sell_amount || 0
          existing.appear_count += 1
          // 如果有多个数据，使用最新的net_buy_ratio（或者可以加权平均，这里简单使用最新的）
          if (item.net_buy_ratio !== undefined && item.net_buy_ratio !== null) {
            existing.net_buy_ratio = item.net_buy_ratio
          }
        } else {
          stockMap.set(code, {
            stock_code: code,
            stock_name: item.stock_name || code,
            net_buy_amount: item.institution_net_buy_amount || 0,
            buy_amount: item.institution_buy_amount || 0,
            sell_amount: item.institution_sell_amount || 0,
            appear_count: 1,
            net_buy_ratio: item.net_buy_ratio, // 从数据库获取净买额占比
          })
        }
      })

      // 为所有筛选出的股票创建数据点（即使当天没有数据，也创建零值数据点）
      finalStocks.forEach((code) => {
        if (stockMap.has(code)) {
          // 有数据的股票，使用实际数据
          const stockData = stockMap.get(code)!
          // 调试信息：检查天龙集团是否被过滤
          if (stockData.stock_code === '300063') {
            console.log('[热力图数据] 天龙集团数据处理:', {
              date,
              stock_code: stockData.stock_code,
              stock_name: stockData.stock_name,
              net_buy_amount: stockData.net_buy_amount,
            })
          }
          heatmapItems.push({
            date,
            ...stockData,
          })
        } else {
          // 没有数据的股票，创建零值数据点
          heatmapItems.push({
            date,
            stock_code: code,
            stock_name: stockNameMap.get(code) || code,
            net_buy_amount: 0,
            buy_amount: 0,
            sell_amount: 0,
            appear_count: 0,
            net_buy_ratio: undefined, // 没有数据时占比也为空
          })
        }
      })
    })

    // 如果当前在 chart tab，等待 DOM 完全渲染后再更新数据
    if (statisticsSubTab.value === 'chart') {
      await nextTick()
      // 额外等待一小段时间，确保图表容器已完全渲染
      await new Promise(resolve => setTimeout(resolve, 50))
    }

    heatmapData.value = heatmapItems.sort((a, b) => {
      // 先按日期排序，再按净买入金额排序
      const dateCompare = a.date.localeCompare(b.date)
      if (dateCompare !== 0) return dateCompare
      return Math.abs(b.net_buy_amount) - Math.abs(a.net_buy_amount)
    })
    
    // 调试信息：输出热力图数据统计
    const stockCount = new Set(heatmapData.value.map(item => item.stock_code)).size
    const uniqueStocks = Array.from(new Set(heatmapData.value.map(item => item.stock_code)))
    console.log('[热力图] 数据统计:', {
      总数据点: heatmapData.value.length,
      股票数量: stockCount,
      期望股票数量: finalStocks.length,
      日期范围: `${startDate.format('YYYY-MM-DD')} 至 ${endDate.format('YYYY-MM-DD')}`,
      显示的股票: uniqueStocks.map(code => {
        const item = heatmapData.value.find(i => i.stock_code === code)
        return `${code}(${item?.stock_name || code})`
      }),
      finalStocks列表: finalStocks,
      缺失的股票: finalStocks.filter(code => !uniqueStocks.includes(code)),
    })
    
    // 如果股票数量不足，检查原因
    if (stockCount < finalStocks.length) {
      console.warn('[热力图] 警告: 股票数量不足', {
        期望数量: finalStocks.length,
        实际数量: stockCount,
        缺失的股票: finalStocks.filter(code => !uniqueStocks.includes(code)),
      })
    }
    
    // 检查天龙集团是否在数据中
    const tianlongData = heatmapData.value.filter(item => 
      item.stock_code === '300063' || item.stock_name.includes('天龙集团')
    )
    if (tianlongData.length > 0) {
      console.log('[热力图] 找到天龙集团数据:', tianlongData)
    } else {
      console.warn('[热力图] 未找到天龙集团数据，可能原因：1)上榜次数不够多 2)日期范围内无数据')
    }
  } catch (e) {
    console.error('获取热力图数据失败', e)
    heatmapData.value = []
  }
}

// 判断是否是交易日（排除周末）
const isTradingDay = (date: string): boolean => {
  const weekday = dayjs(date).day()
  // 0 = 周日, 6 = 周六，排除周末
  return weekday !== 0 && weekday !== 6
}

// 获取净买额占比top10折线图数据
const fetchNetBuyRatioLineChartData = async () => {
  if (!statisticsStartDate.value || !statisticsEndDate.value) {
    netBuyRatioLineChartData.value = []
    return
  }

  try {
    const startDate = dayjs(statisticsStartDate.value)
    const endDate = dayjs(statisticsEndDate.value)
    const days = endDate.diff(startDate, 'day') + 1

    // 如果天数太多，不显示折线图
    if (days > 60) {
      netBuyRatioLineChartData.value = []
      return
    }

    // 1. 获取汇总统计数据，按净买额占比排序，取top10
    const aggregatedParams: any = {
      start_date: statisticsStartDate.value,
      end_date: statisticsEndDate.value,
      stock_code: statisticsStockCode.value || undefined,
      stock_name: statisticsStockName.value || undefined,
      min_appear_count: minAppearCount.value ? parseInt(minAppearCount.value) : undefined,
      max_appear_count: maxAppearCount.value ? parseInt(maxAppearCount.value) : undefined,
      min_total_net_buy_amount: minTotalNetBuyAmount.value ? parseFloat(minTotalNetBuyAmount.value) * 10000 : undefined,
      max_total_net_buy_amount: maxTotalNetBuyAmount.value ? parseFloat(maxTotalNetBuyAmount.value) * 10000 : undefined,
      sort_by: 'net_buy_ratio',
      order: 'desc',
      page: 1,
      page_size: 10, // 只取top10
    }

    const aggregatedRes = await institutionTradingApi.getAggregated(aggregatedParams)
    
    if (!aggregatedRes.items || aggregatedRes.items.length === 0) {
      netBuyRatioLineChartData.value = []
      return
    }

    // 2. 获取top10股票的代码列表
    const top10Stocks = aggregatedRes.items.map(item => ({
      stock_code: item.stock_code,
      stock_name: item.stock_name,
    }))

    // 3. 获取这些股票在时间范围内的每日数据（只获取交易日）
    const dailyDataPromises: Array<Promise<any[]>> = []
    const tradingDates: string[] = []
    
    for (let i = 0; i < days; i++) {
      const date = startDate.add(i, 'day').format('YYYY-MM-DD')
      // 只获取交易日的数据，跳过周末
      if (isTradingDay(date)) {
        tradingDates.push(date)
        dailyDataPromises.push(fetchAllListData(date))
      }
    }

    const dailyResults = await Promise.all(dailyDataPromises)

    // 4. 按股票组织数据（保存详细信息）
    const stockDataMap = new Map<string, Array<{
      date: string
      net_buy_ratio: number | null
      institution_buy_amount?: number
      institution_sell_amount?: number
      institution_net_buy_amount?: number
      market_total_amount?: number
    }>>()
    
    // 初始化每个股票的数据结构
    top10Stocks.forEach(stock => {
      stockDataMap.set(stock.stock_code, [])
    })

    // 填充每日数据（只处理交易日）
    dailyResults.forEach((items, index) => {
      const date = tradingDates[index]
      
      // 跳过非交易日：如果没有数据，直接跳过
      if (!items || items.length === 0) {
        return
      }
      
      // 按股票代码聚合当天的数据（如果同一天同一只股票出现多次，使用最新的net_buy_ratio）
      const stockDailyMap = new Map<string, InstitutionTradingStatisticsItem>()
      items.forEach((item) => {
        if (stockDataMap.has(item.stock_code)) {
          const existing = stockDailyMap.get(item.stock_code)
          // 优先使用有net_buy_ratio的数据，如果都有，使用最新的
          if (!existing) {
            stockDailyMap.set(item.stock_code, item)
          } else if (item.net_buy_ratio !== undefined && item.net_buy_ratio !== null) {
            // 如果新数据有net_buy_ratio，优先使用新数据
            if (existing.net_buy_ratio === undefined || existing.net_buy_ratio === null) {
              stockDailyMap.set(item.stock_code, item)
            } else {
              // 如果都有net_buy_ratio，使用最新的（可以根据需要改为加权平均）
              stockDailyMap.set(item.stock_code, item)
            }
          }
        }
      })

      // 更新每个股票的数据（保存详细信息）
      top10Stocks.forEach(stock => {
        const dailyItem = stockDailyMap.get(stock.stock_code)
        const ratio = dailyItem?.net_buy_ratio !== undefined && dailyItem.net_buy_ratio !== null 
          ? dailyItem.net_buy_ratio 
          : null
        stockDataMap.get(stock.stock_code)!.push({
          date,
          net_buy_ratio: ratio,
          institution_buy_amount: dailyItem?.institution_buy_amount,
          institution_sell_amount: dailyItem?.institution_sell_amount,
          institution_net_buy_amount: dailyItem?.institution_net_buy_amount,
          market_total_amount: dailyItem?.market_total_amount,
        })
      })
    })

    // 5. 转换为折线图数据格式
    const chartData = top10Stocks.map(stock => ({
      stock_code: stock.stock_code,
      stock_name: stock.stock_name,
      data: stockDataMap.get(stock.stock_code) || [],
    }))
    
    // 如果当前在 chart tab，等待 DOM 完全渲染后再更新数据
    if (statisticsSubTab.value === 'chart') {
      await nextTick()
      // 额外等待一小段时间，确保图表容器已完全渲染
      await new Promise(resolve => setTimeout(resolve, 50))
    }
    
    netBuyRatioLineChartData.value = chartData
  } catch (e) {
    console.error('获取净买额占比折线图数据失败', e)
    netBuyRatioLineChartData.value = []
  }
}

// 获取所有聚合数据（处理分页）
const fetchAllAggregatedData = async (startDate: string, endDate: string) => {
  const allItems: any[] = []
  let page = 1
  const pageSize = 100 // 使用最大允许的page_size
  let hasMore = true

  while (hasMore) {
    try {
      const res = await institutionTradingApi.getAggregated({
        start_date: startDate,
        end_date: endDate,
        page,
        page_size: pageSize,
      })
      
      allItems.push(...res.items)
      
      // 如果返回的数据少于pageSize，说明已经是最后一页
      if (res.items.length < pageSize || page >= res.total_pages) {
        hasMore = false
      } else {
        page++
      }
    } catch (e) {
      console.error(`获取第${page}页数据失败`, e)
      hasMore = false
    }
  }

  return allItems
}

// 获取统计汇总

const fetchStatisticsData = async () => {
  try {
    // 时间段查询：使用汇总统计API
    // 如果没有选择日期，使用默认日期（最近5个交易日）
    if (!statisticsStartDate.value || !statisticsEndDate.value) {
      const recentTradingDays = getRecentTradingDays(5)
      statisticsStartDate.value = recentTradingDays.startDate
      statisticsEndDate.value = recentTradingDays.endDate
    }
    
    // 获取当前store中的排序参数
    const currentFilters = institutionTradingStore.aggregatedFilters
    
    const params: any = {
      start_date: statisticsStartDate.value,
      end_date: statisticsEndDate.value,
      stock_code: statisticsStockCode.value || undefined,
      stock_name: statisticsStockName.value || undefined,
      min_appear_count: minAppearCount.value ? parseInt(minAppearCount.value) : undefined,
      max_appear_count: maxAppearCount.value ? parseInt(maxAppearCount.value) : undefined,
      min_total_net_buy_amount: minTotalNetBuyAmount.value ? parseFloat(minTotalNetBuyAmount.value) * 10000 : undefined, // 转换为元
      max_total_net_buy_amount: maxTotalNetBuyAmount.value ? parseFloat(maxTotalNetBuyAmount.value) * 10000 : undefined, // 转换为元
      // 包含排序参数
      sort_by: currentFilters.sort_by,
      order: currentFilters.order,
    }
    
    await institutionTradingStore.fetchAggregated(params)
    
    // 只在统计图tab时才获取图表数据，并使用 nextTick 确保 DOM 已渲染
    if (statisticsSubTab.value === 'chart') {
      // 等待 DOM 更新完成
      await nextTick()
      // 再等待一小段时间确保图表容器已完全渲染
      await new Promise(resolve => setTimeout(resolve, 100))
      
      // 获取热力图数据
      await fetchHeatmapData()
      
      // 再次等待 DOM 更新
      await nextTick()
      await new Promise(resolve => setTimeout(resolve, 100))
      
      // 获取净买额占比折线图数据
      await fetchNetBuyRatioLineChartData()
    }
    
    if (statisticsTableData.value.length === 0 && !statisticsLoading.value) {
      ElMessage.info(`该时间段(${statisticsStartDate.value} 至 ${statisticsEndDate.value})暂无机构交易统计数据`)
    }
  } catch (e: any) {
    ElMessage.error(e?.message || '获取机构交易统计数据失败')
  }
}

const handleStatisticsDateRangeChange = () => {
  institutionTradingStore.setAggregatedFilters({
    start_date: statisticsStartDate.value,
    end_date: statisticsEndDate.value,
  })
  fetchStatisticsData()
}

// 处理上榜次数输入
const handleAppearCountInput = (type: 'min' | 'max', value: string) => {
  // 只允许输入数字
  const numValue = value.replace(/[^\d]/g, '')
  if (type === 'min') {
    minAppearCount.value = numValue
  } else {
    maxAppearCount.value = numValue
  }
}

// 处理累计净买入输入
const handleNetBuyAmountInput = (type: 'min' | 'max', value: string) => {
  // 只允许输入数字和小数点
  const numValue = value.replace(/[^\d.]/g, '').replace(/\.{2,}/g, '.').replace(/(\..*)\./g, '$1')
  if (type === 'min') {
    minTotalNetBuyAmount.value = numValue
  } else {
    maxTotalNetBuyAmount.value = numValue
  }
}

const handleStatisticsSearch = () => {
  institutionTradingStore.setAggregatedPagination(1, statisticsPagination.value.pageSize)
  institutionTradingStore.setAggregatedFilters({
    stock_code: statisticsStockCode.value || undefined,
    stock_name: statisticsStockName.value || undefined,
    min_appear_count: minAppearCount.value ? parseInt(minAppearCount.value) : undefined,
    max_appear_count: maxAppearCount.value ? parseInt(maxAppearCount.value) : undefined,
    min_total_net_buy_amount: minTotalNetBuyAmount.value ? parseFloat(minTotalNetBuyAmount.value) * 10000 : undefined,
    max_total_net_buy_amount: maxTotalNetBuyAmount.value ? parseFloat(maxTotalNetBuyAmount.value) * 10000 : undefined,
  })
  fetchStatisticsData()
}

const handleStatisticsSizeChange = () => {
  institutionTradingStore.setAggregatedPagination(statisticsPagination.value.current, statisticsPagination.value.pageSize)
  fetchStatisticsData()
}

const handleStatisticsPageChange = () => {
  institutionTradingStore.setAggregatedPagination(statisticsPagination.value.current, statisticsPagination.value.pageSize)
  fetchStatisticsData()
}

// 前端字段名到后端排序字段名的映射
const sortFieldMapping: Record<string, string> = {
  'appear_count': 'appear_count',
  'total_net_buy_amount': 'institution_net_buy_amount',
  'total_buy_amount': 'institution_buy_amount',
  'total_sell_amount': 'institution_sell_amount',
  'total_market_amount': 'total_market_amount',
  'net_buy_ratio': 'net_buy_ratio',
}

const handleStatisticsSortChange = (sort: { prop: string; order: 'ascending' | 'descending' | null }) => {
  if (!sort.order) {
    // 取消排序，恢复默认排序
    institutionTradingStore.setAggregatedFilters({
      sort_by: 'appear_count',
      order: 'desc',
    })
  } else {
    // 映射前端字段名到后端字段名
    const backendSortBy = sortFieldMapping[sort.prop] || sort.prop
    const order = sort.order === 'ascending' ? 'asc' : 'desc'
    
    institutionTradingStore.setAggregatedFilters({
      sort_by: backendSortBy,
      order,
    })
  }
  // 重置到第一页并重新获取数据
  institutionTradingStore.setAggregatedPagination(1, statisticsPagination.value.pageSize)
  fetchStatisticsData()
}

const handleReset = () => {
  date.value = dayjs().format('YYYY-MM-DD')
  stockCode.value = ''
  stockName.value = ''
  direction.value = ''
  
  lhbHotStore.setPagination(1, pagination.value.pageSize)
  lhbHotStore.setFilters({
    date: date.value,
    stock_code: undefined,
    stock_name: undefined,
    flag: undefined,
  })
  fetchData()
}

const handleStatisticsReset = () => {
  // 重置为最近5个交易日
  const recentTradingDays = getRecentTradingDays(5)
  statisticsStartDate.value = recentTradingDays.startDate
  statisticsEndDate.value = recentTradingDays.endDate
  statisticsStockCode.value = ''
  statisticsStockName.value = ''
  minAppearCount.value = ''
  maxAppearCount.value = ''
  minTotalNetBuyAmount.value = ''
  maxTotalNetBuyAmount.value = ''
  
  institutionTradingStore.setAggregatedPagination(1, statisticsPagination.value.pageSize)
  institutionTradingStore.setAggregatedFilters({
    start_date: statisticsStartDate.value,
    end_date: statisticsEndDate.value,
    stock_code: undefined,
    stock_name: undefined,
    min_appear_count: undefined,
    max_appear_count: undefined,
    min_total_net_buy_amount: undefined,
    max_total_net_buy_amount: undefined,
    sort_by: 'appear_count', // 重置为默认排序：按上榜次数
    order: 'desc', // 倒序
  })
  fetchStatisticsData()
}

// 工具函数：获取金额样式类
const getAmountClass = (amount: number | undefined | null): string => {
  if (!amount) return ''
  return amount > 0 ? 'amount-positive' : 'amount-negative'
}

// 工具函数：获取涨跌幅样式类
const getPercentClass = (percent: number | undefined | null): string => {
  if (percent === null || percent === undefined) return ''
  return percent > 0 ? 'percent-positive' : 'percent-negative'
}

// 显示上榜明细
const handleShowDetail = async (row: any) => {
  detailStockInfo.value = {
    stock_code: row.stock_code,
    stock_name: row.stock_name,
  }
  detailDialogVisible.value = true
  detailPagination.value.current = 1
  await fetchDetailList()
}

// 获取明细列表
const fetchDetailList = async () => {
  if (!detailStockInfo.value.stock_code || !statisticsStartDate.value || !statisticsEndDate.value) {
    return
  }
  
  detailLoading.value = true
  try {
    const res = await institutionTradingApi.getList({
      start_date: statisticsStartDate.value,
      end_date: statisticsEndDate.value,
      stock_code: detailStockInfo.value.stock_code,
      page: detailPagination.value.current,
      page_size: detailPagination.value.pageSize,
      sort_by: 'date',
      order: 'desc',
    })
    detailList.value = res.items
    detailPagination.value.total = res.total
  } catch (e: any) {
    ElMessage.error(e?.message || '获取上榜明细失败')
    detailList.value = []
    detailPagination.value.total = 0
  } finally {
    detailLoading.value = false
  }
}

const handleDetailSizeChange = () => {
  fetchDetailList()
}

const handleDetailPageChange = () => {
  fetchDetailList()
}

// 龙虎榜数据获取
const fetchLhbData = async () => {
  try {
    const dateStr = lhbDate.value
    if (!dateStr) {
      ElMessage.warning('请选择日期')
      return
    }
    
    await lhbStore.fetchList({
      date: dateStr,
      stock_code: lhbStockCode.value || undefined,
      stock_name: lhbStockName.value || undefined,
    })
    
    if (lhbTableData.value.length === 0 && !lhbLoading.value) {
      ElMessage.info(`该日期(${dateStr})暂无龙虎榜数据`)
    }
  } catch (error: any) {
    const errorMsg = error?.response?.data?.detail || error?.message || '获取数据失败，请稍后重试'
    ElMessage.error(errorMsg)
  }
}

const handleLhbDateChange = () => {
  lhbStore.setFilters({ date: lhbDate.value })
  fetchLhbData()
}

const handleLhbSearch = () => {
  lhbStore.setPagination(1, lhbPagination.value.pageSize)
  fetchLhbData()
}

const handleLhbSizeChange = () => {
  fetchLhbData()
}

const handleLhbPageChange = () => {
  fetchLhbData()
}

// 时间跨度统计相关函数
const handleLhbQueryModeChange = () => {
  if (lhbQueryMode.value === 'range') {
    // 切换到时间跨度模式，设置默认日期范围（最近5个交易日）
    const recentTradingDays = getRecentTradingDays(5)
    lhbDateRange.value = [recentTradingDays.startDate, recentTradingDays.endDate]
    lhbStatisticsPagination.value.current = 1
    fetchLhbStatisticsData()
  } else {
    // 切换到单日模式，重置为今天
    lhbDate.value = dayjs().format('YYYY-MM-DD')
    fetchLhbData()
  }
}

const handleLhbDateRangeChange = () => {
  lhbStatisticsPagination.value.current = 1
  fetchLhbStatisticsData()
}

const fetchLhbStatisticsData = async () => {
  if (!lhbDateRange.value || lhbDateRange.value.length !== 2) {
    ElMessage.warning('请选择日期范围')
    return
  }
  
  lhbStatisticsLoading.value = true
  try {
    const res = await lhbApi.getStocksStatistics({
      start_date: lhbDateRange.value[0],
      end_date: lhbDateRange.value[1],
      stock_code: lhbStockCode.value || undefined,
      stock_name: lhbStockName.value || undefined,
      page: lhbStatisticsPagination.value.current,
      page_size: lhbStatisticsPagination.value.pageSize,
      sort_by: lhbStatisticsSortBy.value,
      order: lhbStatisticsOrder.value,
    })
    
    lhbStatisticsTableData.value = res.items
    lhbStatisticsPagination.value.total = res.total
    
    if (res.items.length === 0) {
      ElMessage.info('该时间范围内暂无上榜个股数据')
    }
  } catch (error: any) {
    const errorMsg = error?.response?.data?.detail || error?.message || '获取统计数据失败'
    ElMessage.error(errorMsg)
    lhbStatisticsTableData.value = []
    lhbStatisticsPagination.value.total = 0
  } finally {
    lhbStatisticsLoading.value = false
  }
}

const handleLhbStatisticsSearch = () => {
  lhbStatisticsPagination.value.current = 1
  fetchLhbStatisticsData()
}

const handleLhbStatisticsReset = () => {
  const recentTradingDays = getRecentTradingDays(5)
  lhbDateRange.value = [recentTradingDays.startDate, recentTradingDays.endDate]
  lhbStockCode.value = ''
  lhbStockName.value = ''
  lhbStatisticsPagination.value.current = 1
  lhbStatisticsSortBy.value = 'appear_count'
  lhbStatisticsOrder.value = 'desc'
  fetchLhbStatisticsData()
}

const handleLhbStatisticsSortChange = (sort: { prop: string; order: 'ascending' | 'descending' | null }) => {
  if (!sort.prop || !sort.order) {
    lhbStatisticsSortBy.value = 'appear_count'
    lhbStatisticsOrder.value = 'desc'
  } else {
    lhbStatisticsSortBy.value = sort.prop
    lhbStatisticsOrder.value = sort.order === 'ascending' ? 'asc' : 'desc'
  }
  lhbStatisticsPagination.value.current = 1
  fetchLhbStatisticsData()
}

const handleLhbStatisticsSizeChange = () => {
  fetchLhbStatisticsData()
}

const handleLhbStatisticsPageChange = () => {
  fetchLhbStatisticsData()
}

const handleLhbSortChange = (sort: { prop: string; order: 'ascending' | 'descending' | null }) => {
  const sortBy = sort.order ? sort.prop : undefined
  const order = sort.order === 'ascending' ? 'asc' : sort.order === 'descending' ? 'desc' : undefined
  lhbStore.setFilters({
    sort_by: sortBy,
    order,
  })
  fetchLhbData()
}

const handleLhbReset = () => {
  lhbDate.value = dayjs().format('YYYY-MM-DD')
  lhbStockCode.value = ''
  lhbStockName.value = ''
  
  lhbStore.setPagination(1, lhbPagination.value.pageSize)
  lhbStore.setFilters({
    date: lhbDate.value,
    stock_code: undefined,
    stock_name: undefined,
  })
  fetchLhbData()
}

// 解析概念字符串为数组（支持逗号、空格分隔）
const getConceptList = (conceptStr: string | null | undefined): string[] => {
  if (!conceptStr) return []
  return conceptStr
    .split(/[,，\s]+/)
    .map((c) => c.trim())
    .filter((c) => c.length > 0)
}

// 活跃营业部数据获取
const fetchActiveBranchData = async () => {
  activeBranchLoading.value = true
  try {
    const res = await lhbApi.getActiveBranchList({
      date: activeBranchDate.value || undefined,
      page: activeBranchPagination.value.current,
      page_size: activeBranchPagination.value.pageSize,
      institution_name: activeBranchName.value || undefined,
      institution_code: activeBranchCode.value || undefined,
      buy_stock_name: activeBranchBuyStockName.value || undefined,
      sort_by: activeBranchSortBy.value,
      order: activeBranchOrder.value,
    })
    activeBranchTableData.value = res.items
    activeBranchPagination.value.total = res.total
    
    if (res.items.length === 0 && !activeBranchLoading.value) {
      ElMessage.info('暂无活跃营业部数据')
    }
  } catch (error: any) {
    const errorMsg = error?.response?.data?.detail || error?.message || '获取活跃营业部数据失败'
    ElMessage.error(errorMsg)
    activeBranchTableData.value = []
    activeBranchPagination.value.total = 0
  } finally {
    activeBranchLoading.value = false
  }
}

const handleActiveBranchDateChange = () => {
  activeBranchPagination.value.current = 1
  fetchActiveBranchData()
}

const handleActiveBranchSearch = () => {
  activeBranchPagination.value.current = 1
  fetchActiveBranchData()
}

const handleActiveBranchReset = () => {
  activeBranchDate.value = ''
  activeBranchName.value = ''
  activeBranchCode.value = ''
  activeBranchBuyStockName.value = ''
  activeBranchSortBy.value = 'net_amount'
  activeBranchOrder.value = 'desc'
  activeBranchPagination.value.current = 1
  fetchActiveBranchData()
}

const handleActiveBranchSizeChange = () => {
  fetchActiveBranchData()
}

const handleActiveBranchPageChange = () => {
  fetchActiveBranchData()
}

const handleActiveBranchSortChange = (sort: { prop: string; order: 'ascending' | 'descending' | null }) => {
  activeBranchSortBy.value = sort.order ? sort.prop : 'net_amount'
  activeBranchOrder.value = sort.order === 'ascending' ? 'asc' : sort.order === 'descending' ? 'desc' : 'desc'
  // 重置到第一页
  activeBranchPagination.value.current = 1
  // 重新获取数据
  fetchActiveBranchData()
}

// 营业部交易详情相关函数
const handleViewBranchDetail = (row: ActiveBranchItem) => {
  if (!row.institution_code) {
    ElMessage.warning('该营业部没有代码，无法查看详情')
    return
  }
  selectedBranchCode.value = row.institution_code
  selectedBranchName.value = row.institution_name || ''
  branchDetailDialogVisible.value = true
  branchDetailPagination.value.current = 1
  fetchBranchDetailData()
}

const fetchBranchDetailData = async () => {
  if (!selectedBranchCode.value) return
  
  branchDetailLoading.value = true
  try {
    const res = await lhbApi.getActiveBranchDetail(selectedBranchCode.value, {
      date: branchDetailDate.value || undefined,
      page: branchDetailPagination.value.current,
      page_size: branchDetailPagination.value.pageSize,
      stock_code: branchDetailStockCode.value || undefined,
      stock_name: branchDetailStockName.value || undefined,
      sort_by: branchDetailSortBy.value,
      order: branchDetailOrder.value,
    })
    branchDetailTableData.value = res.items
    branchDetailPagination.value.total = res.total
  } catch (error: any) {
    console.error('获取营业部交易详情失败:', error)
    ElMessage.error(error?.response?.data?.detail || '获取营业部交易详情失败')
    branchDetailTableData.value = []
    branchDetailPagination.value.total = 0
  } finally {
    branchDetailLoading.value = false
  }
}

const handleBranchDetailDateChange = () => {
  branchDetailPagination.value.current = 1
  fetchBranchDetailData()
}

const handleBranchDetailSearch = () => {
  branchDetailPagination.value.current = 1
  fetchBranchDetailData()
}

// 买入股票统计相关函数
const fetchBuyStocksStatisticsData = async () => {
  buyStocksStatisticsLoading.value = true
  try {
    console.log('[买入股票统计] 开始请求，参数:', {
      date: buyStocksStatisticsDate.value || undefined,
      page: buyStocksStatisticsPagination.value.current,
      page_size: buyStocksStatisticsPagination.value.pageSize,
    })
    
    const res = await lhbApi.getBuyStocksStatistics({
      date: buyStocksStatisticsDate.value || undefined,
      page: buyStocksStatisticsPagination.value.current,
      page_size: buyStocksStatisticsPagination.value.pageSize,
    })
    
    // 确保数据正确赋值
    const items = Array.isArray(res?.items) ? res.items : []
    const total = typeof res?.total === 'number' ? res.total : 0
    
    console.log('[买入股票统计] API响应:', {
      res: res,
      resType: typeof res,
      hasItems: !!res?.items,
      itemsType: Array.isArray(res?.items),
      items: items,
      itemsLength: items.length,
      total: total,
    })
    
    buyStocksStatisticsTableData.value = items
    buyStocksStatisticsPagination.value.total = total
    
    console.log('[买入股票统计] 数据赋值后:', {
      tableData: buyStocksStatisticsTableData.value,
      tableDataLength: buyStocksStatisticsTableData.value.length,
      pagination: buyStocksStatisticsPagination.value,
    })
    
    if (items.length === 0) {
      ElMessage.info('暂无买入股票统计数据')
    } else {
      console.log('[买入股票统计] 数据已成功加载，共', items.length, '条记录')
    }
  } catch (error: any) {
    console.error('[买入股票统计] 请求失败:', error)
    const errorMsg = error?.response?.data?.detail || error?.message || '获取买入股票统计失败'
    ElMessage.error(errorMsg)
    buyStocksStatisticsTableData.value = []
    buyStocksStatisticsPagination.value.total = 0
  } finally {
    buyStocksStatisticsLoading.value = false
  }
}

const handleBuyStocksStatisticsDateChange = () => {
  buyStocksStatisticsPagination.value.current = 1
  fetchBuyStocksStatisticsData()
}

const handleBuyStocksStatisticsSearch = () => {
  buyStocksStatisticsPagination.value.current = 1
  fetchBuyStocksStatisticsData()
}

const handleBuyStocksStatisticsReset = () => {
  buyStocksStatisticsDate.value = ''
  buyStocksStatisticsPagination.value.current = 1
  fetchBuyStocksStatisticsData()
}

const handleBuyStocksStatisticsSizeChange = () => {
  fetchBuyStocksStatisticsData()
}

const handleBuyStocksStatisticsPageChange = () => {
  fetchBuyStocksStatisticsData()
}

// 买入股票对应的营业部详情相关函数
const handleShowBuyStockBranches = (row: { stock_name: string; appear_count: number }) => {
  selectedStockName.value = row.stock_name
  buyStockBranchesDialogVisible.value = true
  buyStockBranchesPagination.value.current = 1
  buyStockBranchesDate.value = buyStocksStatisticsDate.value || ''
  buyStockBranchesSortBy.value = 'date'
  buyStockBranchesOrder.value = 'desc'
  fetchBuyStockBranchesData()
}

const fetchBuyStockBranchesData = async () => {
  if (!selectedStockName.value) return
  
  buyStockBranchesLoading.value = true
  try {
    const res = await lhbApi.getActiveBranchDetailByStockName(selectedStockName.value, {
      date: buyStockBranchesDate.value || undefined,
      page: buyStockBranchesPagination.value.current,
      page_size: buyStockBranchesPagination.value.pageSize,
      sort_by: buyStockBranchesSortBy.value,
      order: buyStockBranchesOrder.value,
    })
    buyStockBranchesTableData.value = res.items
    buyStockBranchesPagination.value.total = res.total
    
    // 更新统计数据
    if (res.statistics) {
      buyStockBranchesStats.value = {
        buyBranchCount: res.statistics.buy_branch_count,
        sellBranchCount: res.statistics.sell_branch_count,
        totalBuyAmount: res.statistics.total_buy_amount,
        totalSellAmount: res.statistics.total_sell_amount,
      }
    } else {
      // 如果没有统计信息，重置为0
      buyStockBranchesStats.value = {
        buyBranchCount: 0,
        sellBranchCount: 0,
        totalBuyAmount: 0,
        totalSellAmount: 0,
      }
    }
    
    if (res.items.length === 0 && !buyStockBranchesLoading.value) {
      ElMessage.info('暂无活跃营业部交易详情')
    }
  } catch (error: any) {
    const errorMsg = error?.response?.data?.detail || error?.message || '获取活跃营业部交易详情失败'
    ElMessage.error(errorMsg)
    buyStockBranchesTableData.value = []
    buyStockBranchesPagination.value.total = 0
  } finally {
    buyStockBranchesLoading.value = false
  }
}

const handleBuyStockBranchesDateChange = () => {
  buyStockBranchesPagination.value.current = 1
  fetchBuyStockBranchesData()
}

const handleBuyStockBranchesReset = () => {
  buyStockBranchesDate.value = buyStocksStatisticsDate.value || ''
  buyStockBranchesSortBy.value = 'date'
  buyStockBranchesOrder.value = 'desc'
  buyStockBranchesPagination.value.current = 1
  fetchBuyStockBranchesData()
}

const handleBuyStockBranchesSortChange = (sort: { prop: string; order: 'ascending' | 'descending' | null }) => {
  buyStockBranchesSortBy.value = sort.order ? sort.prop : 'date'
  buyStockBranchesOrder.value = sort.order === 'ascending' ? 'asc' : sort.order === 'descending' ? 'desc' : 'desc'
  buyStockBranchesPagination.value.current = 1
  fetchBuyStockBranchesData()
}

const handleBuyStockBranchesSizeChange = () => {
  fetchBuyStockBranchesData()
}

const handleBuyStockBranchesPageChange = () => {
  fetchBuyStockBranchesData()
}

const handleViewBranchDetailFromBuyStock = (row: ActiveBranchDetailItem) => {
  if (!row.institution_code) {
    ElMessage.warning('该营业部没有代码，无法查看详情')
    return
  }
  // 关闭当前对话框
  buyStockBranchesDialogVisible.value = false
  // 打开营业部详情对话框
  selectedBranchCode.value = row.institution_code
  selectedBranchName.value = row.institution_name || ''
  branchDetailDialogVisible.value = true
  branchDetailPagination.value.current = 1
  fetchBranchDetailData()
}

const handleBranchDetailReset = () => {
  branchDetailDate.value = ''
  branchDetailStockCode.value = ''
  branchDetailStockName.value = ''
  branchDetailSortBy.value = 'date'
  branchDetailOrder.value = 'desc'
  branchDetailPagination.value.current = 1
  fetchBranchDetailData()
}

const handleBranchDetailSizeChange = () => {
  fetchBranchDetailData()
}

const handleBranchDetailPageChange = () => {
  fetchBranchDetailData()
}

const handleBranchDetailSortChange = (sort: { prop: string; order: 'ascending' | 'descending' | null }) => {
  branchDetailSortBy.value = sort.order ? sort.prop : 'date'
  branchDetailOrder.value = sort.order === 'ascending' ? 'asc' : sort.order === 'descending' ? 'desc' : 'desc'
  branchDetailPagination.value.current = 1
  fetchBranchDetailData()
}

// 监听主菜单切换，加载对应数据
watch(activeMainMenu, async (newMenu, oldMenu) => {
  // 避免初始化时重复加载（onMounted 会处理初始加载）
  if (oldMenu === undefined) {
    return
  }
  
  if (newMenu === 'statistics') {
    // 切换到机构交易统计时，根据当前tab加载数据
    if (statisticsSubTab.value === 'chart') {
      await nextTick()
      await new Promise(resolve => setTimeout(resolve, 100))
      if (statisticsTableData.value.length > 0) {
        await fetchHeatmapData()
        await nextTick()
        await fetchNetBuyRatioLineChartData()
      } else {
        fetchStatisticsData()
      }
    } else {
      fetchStatisticsData()
    }
  } else if (newMenu === 'activeBranch') {
    // 切换到活跃营业部时，根据当前tab加载数据
    if (activeBranchSubTab.value === 'buyStocks') {
      fetchBuyStocksStatisticsData()
    } else {
      fetchActiveBranchData()
    }
  } else if (newMenu === 'stocks') {
    fetchLhbData()
  } else if (newMenu === 'detail') {
    fetchData()
  }
}, { immediate: false })

// 监听统计图 tab 切换
watch(statisticsSubTab, async (newTab) => {
  if (activeMainMenu.value === 'statistics') {
    if (newTab === 'chart') {
      // 等待 DOM 更新完成
      await nextTick()
      await new Promise(resolve => setTimeout(resolve, 100))
      
      // 如果数据已存在，直接使用；否则获取数据
      if (statisticsTableData.value.length > 0) {
        await fetchHeatmapData()
        await nextTick()
        await fetchNetBuyRatioLineChartData()
      } else {
        fetchStatisticsData()
      }
    } else if (newTab === 'detail') {
      fetchStatisticsData()
    }
  }
}, { immediate: false })

// 监听活跃营业部子tab切换
watch(activeBranchSubTab, (newTab) => {
  if (activeMainMenu.value === 'activeBranch') {
    if (newTab === 'buyStocks') {
      fetchBuyStocksStatisticsData()
    } else if (newTab === 'branchInfo') {
      fetchActiveBranchData()
    }
  }
}, { immediate: false })

// 监听路由变化，更新活动菜单
watch(() => route.query.menu, (menu) => {
  const validMenus = ['statistics', 'activeBranch', 'stocks', 'detail']
  if (menu && typeof menu === 'string' && validMenus.includes(menu) && activeMainMenu.value !== menu) {
    handleMainMenuChange(menu)
  }
}, { immediate: true })

onMounted(() => {
  // 根据初始主菜单项加载数据
  if (activeMainMenu.value === 'statistics') {
    if (statisticsSubTab.value === 'chart') {
      fetchStatisticsData()
    } else {
      fetchStatisticsData()
    }
  } else if (activeMainMenu.value === 'activeBranch') {
    if (activeBranchSubTab.value === 'buyStocks') {
      fetchBuyStocksStatisticsData()
    } else {
      fetchActiveBranchData()
    }
  } else if (activeMainMenu.value === 'stocks') {
    fetchLhbData()
  } else if (activeMainMenu.value === 'detail') {
    fetchData()
  }
})
</script>

<style scoped>
.lhb-hot {
  height: 100%;
}

.lhb-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.lhb-card :deep(.el-card__body) {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 0;
}

.lhb-layout {
  width: 100%;
  height: 100%;
  overflow: hidden;
}

.lhb-content {
  width: 100%;
  height: 100%;
  background-color: #fff;
  padding: 12px;
  overflow-y: auto;
}

.content-section {
  width: 100%;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .lhb-content {
    padding: 12px;
  }
}

.filter-bar {
  margin-bottom: 16px;
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-input {
  width: 200px;
}

.filter-input-small {
  width: 150px;
}

.date-separator {
  margin: 0 8px;
  color: #909399;
  font-size: 14px;
}

.date-separator-small {
  margin: 0 4px;
  color: #c0c4cc;
  font-size: 12px;
}

/* 内联过滤组 */
.filter-inline-group {
  display: flex;
  align-items: center;
  gap: 4px;
  white-space: nowrap;
}

.filter-inline-label {
  font-size: 14px;
  color: #606266;
  margin-right: 4px;
}

.filter-number-input-small {
  width: 100px;
}

.range-separator {
  margin: 0 4px;
  color: #909399;
}

.range-separator-small {
  margin: 0 4px;
  color: #c0c4cc;
}

/* 表格样式 */
.detail-table,
.statistics-table,
.active-branch-table {
  margin-top: 16px;
}

.date-range {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 13px;
}

.date-range span:first-child {
  color: #303133;
}

.date-range span:last-child {
  color: #909399;
  font-size: 12px;
}

/* 金额样式 */
.amount-positive {
  color: #f56c6c;
  font-weight: 500;
}

.amount-negative {
  color: #67c23a;
  font-weight: 500;
}

/* 涨跌幅样式 */
.percent-positive {
  color: #f56c6c;
}

.percent-negative {
  color: #67c23a;
}

.change-percent-range {
  display: flex;
  align-items: center;
  font-size: 13px;
}

/* 上榜次数按钮样式 */
.appear-count-btn {
  padding: 0;
  height: auto;
}

.appear-count-btn .el-tag {
  transition: all 0.3s;
  cursor: pointer;
}

.appear-count-btn:hover .el-tag {
  background-color: #409eff;
  color: #fff;
  border-color: #409eff;
  transform: scale(1.05);
}

/* 分页样式 */
.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
  width: 100%;
  overflow-x: auto;
}

.pagination {
  flex-shrink: 0;
}

.lhb-table {
  margin-top: 16px;
}

.institution-detail {
  padding: 10px;
  background-color: #f5f7fa;
}

.text-gray {
  color: #909399;
}

.appear-count {
  font-weight: 600;
  color: #409eff;
}

.buy-stocks-statistics-table {
  margin-top: 16px;
}

.concept-tags {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
}



.trend-up {
  color: #f56c6c;
}

.trend-down {
  color: #67c23a;
}

.trend-same {
  color: #909399;
}

/* 热力图 */
.heatmap-chart-card {
  margin-bottom: 20px;
}

.heatmap-chart {
  width: 100%;
  min-height: 700px; /* 增加最小高度，确保能显示20个股票 */
  height: auto;
}

.heatmap-legend {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid #EBEEF5;
  flex-wrap: wrap;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #606266;
}

.legend-color {
  width: 16px;
  height: 16px;
  border-radius: 2px;
  display: inline-block;
}

/* 折线图 */
.line-chart-card {
  margin-bottom: 20px;
}

.line-chart {
  width: 100%;
  min-height: 500px;
  height: auto;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.heatmap-controls {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.no-heatmap-data {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 400px;
  color: #909399;
  font-size: 14px;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .filter-inline-group {
    flex-wrap: wrap;
  }
  
  .filter-inline-label {
    width: 100%;
    margin-bottom: 4px;
  }
}

@media (max-width: 768px) {
  .filter-bar {
    flex-direction: column;
    align-items: stretch;
  }
  
  .filter-group {
    width: 100%;
  }
  
  .filter-input,
  .filter-input-small {
    width: 100%;
  }
  
  .filter-inline-group {
    width: 100%;
    flex-wrap: wrap;
  }
  
  .filter-number-input-small {
    flex: 1;
    min-width: 80px;
  }
}
</style>

