import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
# from sklearn import preprocessing as pre

################################################################################
#
#                      Config the output display options.                    
#
################################################################################

# Show a 20x30 grid by default and unlimit the width
pd.set_option('display.max_columns', 20)
pd.set_option('display.max_rows', 30)
pd.set_option('display.width', 100)

# Ensure large numbers are readable (round floats if any)
pd.options.display.float_format = '{:,.0f}'.format

# Set figure size for any graphs
# plt.rcParams['figure.figsize'] = (12, 10)

# Set the source data directory location
SOURCE_DATA_FN = "demo.csv"


def extract(*args, **kwargs) -> pd.DataFrame:
    def _checkNaNs(df: pd.DataFrame):
        pass
        #print("Running NaN checks...")
        #print("NaN sum on cols:")
        #print(df.isna().sum())

    def _encodeStringFields(df: pd.DataFrame):
        print("Encoding string fields. New encodings will be appended.")

    df = pd.read_csv(SOURCE_DATA_FN)
    _checkNaNs(df)

    return df


def aggAndUnstack(df: pd.DataFrame) -> pd.DataFrame:
    return df.agg({"TotMins": sum}).unstack().reset_index()


def appendGTs(df: pd.DataFrame, sortGT=False, gtRowTop=False) -> pd.DataFrame:
    if gtRowTop:
        appendGTRow(df, gtRowTop=True)
    else:
        # append a GT col
        appendGTCol(df)
        
        # note sort first otherwise the added row will be sorted too!
        if sortGT:
            df = df.sort_values(by=[('', "Grand Total")], ascending=False)

        df = appendGTRow(df, gtRowTop=False)

    return df


def appendGTCol(df: pd.DataFrame) -> pd.DataFrame:
    df["", "Grand Total"] = df.sum(axis=1)
    return df


def appendGTRow(df: pd.DataFrame, gtRowTop=False) -> pd.DataFrame:
    if gtRowTop:
        # GT row at top
        _df = df.sum(numeric_only=True).unstack()
        _df.columns = df.columns
        _df.index.name = "__"
        df = pd.concat([_df, df])
    else:
        # GT row at bottom
        df = df.append(pd.Series(df.sum(numeric_only=True), name="Grand Total"))

    return df


def createTableOne(srcData: pd.DataFrame) -> pd.DataFrame:
    # Exact multi-indexing and level naming to use
    df1_index = [('State', 'State1'),
                 ('State', 'State2'),
                 ('State', 'State3'),
                 ('State', 'State4')]
    level_names = ['TotMins', 'Item']

    df1 = srcData.copy()
    df1 = df1[["Item", "State", "TotMins"]]

    df1 = aggAndUnstack(df1.groupby(["Item", "State"]))
    
    # correct our multi-index
    df1.set_index("Item", inplace=True)
    df1.index.name = None  # remove index name for prettier formatting
    df1.columns = pd.MultiIndex.from_tuples(df1_index, names=level_names)

    df1 = appendGTs(df1, sortGT=True)

    return df1


def createTableTwo(srcData: pd.DataFrame) -> pd.DataFrame:
    # Exact multi-indexing and level naming to use
    df2_index = [('State', 'State1'),
                 ('State', 'State2'),
                 ('State', 'State3'),
                 ('State', 'State4')]
    level_names = ['TotMins', 'Item']

    df2 = srcData.copy()
    df2 = df2[["ItemGroup", "Item", "State", "TotMins"]]

    # split into groups and aggGroup our data
    df2_g1 = df2.where(df2.ItemGroup == "ItemGroup1").dropna()
    df2_g1 = aggAndUnstack(df2_g1.groupby(["Item", "State"]))
    df2_g2 = df2.where(df2.ItemGroup == "ItemGroup2").dropna()
    df2_g2 = aggAndUnstack(df2_g2.groupby(["Item", "State"]))
    
    # correct our multi-index
    df2_g1.set_index("Item", inplace=True)
    df2_g2.set_index("Item", inplace=True)

    # TODO: Update index name ItemGroup2/1 and remove from index vals
    df2_g1.index.name = None  # remove index name for prettier formatting
    df2_g2.index.name = None

    df2_g1.columns = pd.MultiIndex.from_tuples(df2_index, names=level_names)
    df2_g2.columns = pd.MultiIndex.from_tuples(df2_index, names=level_names)

    # insert totals per state at 1st row
    df2_g1 = appendGTs(df2_g1, gtRowTop=True)
    df2_g2 = appendGTs(df2_g2, gtRowTop=True)

    g1_index = pd.Index(["ItemGroup1"] + df2_g1.index.tolist()[1:])
    g2_index = pd.Index(["ItemGroup2"] + df2_g2.index.tolist()[1:])
    
    df2_g1.set_index(g1_index, inplace=True)
    df2_g2.set_index(g2_index, inplace=True)

    # rejoin tables and append final GT column on all
    df2 = pd.concat([df2_g1, df2_g2])
    df2 = appendGTs(df2)
    return df2


def createTableThree(srcData: pd.DataFrame) -> list:
    # Exact multi-indexing and level naming to use
    df3_index = [('State', 'State1'),
                 ('State', 'State2'),
                 ('State', 'State3'),
                 ('State', 'State4')]
    level_names = ['', 'Week']

    df3 = srcData.copy()
    df3 = df3[["Week", "Item", "State", "TotMins"]]
    df3 = df3.where(df3.Item == "Item04").dropna()

    # agg group and drop the item (constant) col
    df3 = df3.groupby(["State", "Week"]).agg({"TotMins": sum}).reset_index()
    # reshape by pivoting and update our index
    df3 = df3.pivot(index="Week", columns="State")
    df3.index.name = "TotMins"  # add custom index name
    df3.columns = pd.MultiIndex.from_tuples(df3_index, names=level_names)
    
    # add the GT col
    df3 = appendGTCol(df3)

    # create the subtable % of Mins By State
    subname = "% of Mins By State"
    df3_perc = df3.copy()
    df3_perc.index.name = subname

    df3_perc = df3_perc.apply(lambda p: 100 * (p / df3_perc[("", "Grand Total")]))
    # df3_final = pd.concat([df3, df3_perc], keys=[df3.index.names, df3_perc.index.names])
    df3_perc = df3_perc.append(
        pd.Series(df3.sum(numeric_only=True), name="Total TotMins"))
    df3_perc = df3_perc.append(
        pd.Series(df3.sum(numeric_only=True), name=("Total " + subname)))

    # updat the totals perc row as perc
    y = df3_perc.iloc[-1].tolist()
    for i in range(len(y)):
        y[i] = 100 * y[i] / y[-1]
    df3_perc.iloc[-1] = pd.Series(y)

    #df3_final.set_index(pd.Index(new_index), inplace=True)
    df_titles = pd.DataFrame(columns=["Item", "Item04"])
    retData = [df_titles, df3, df3_perc]
    return retData
    

def createTableFour(srcData: pd.DataFrame) -> list:
    # Exact multi-indexing and level naming to use
    df4_index = [('Market', 'Market03'),
                 ('Market', 'Market06'),
                 ('Market', 'Market09'),
                 ('Market', 'Market14'),
                 ('Market', 'Market20'),
                 ('Market', 'Grand Total')]
    level_names = ['AvgMins/Psn', 'Week']

    df4 = srcData.copy()
    df4 = df4[["Week", "Item", "State", "TotMins", "Market", "TotPeople"]]
    df4 = df4.where(df4.Item == "Item07").where(df4.State == "State4").dropna()

    df4 = df4.groupby(["Week", "Market"]).agg(
        {
            "TotMins": sum,
            "TotPeople": sum
        }).reset_index()

    # create a multi index in columnwise direction, collapse this with div-op
    df4 = df4.pivot(index=["Week"], columns=["Market"])
    # append GT cols for each column group
    df4["TotPeople", "Grand Total"] = df4["TotPeople"].sum(axis=1)
    df4["TotMins", "Grand Total"] = df4["TotMins"].sum(axis=1)

    df4 = df4.append(pd.Series(df4.sum(numeric_only=True), name="Grand Total"))
    df4 = df4["TotMins"] / df4["TotPeople"]
    df4.columns = pd.Index(df4_index)
    df4.columns.names = level_names
    df4.index.name = None

    df_titles = pd.DataFrame(columns=["Item", "Item07"])
    retData = [df_titles, df4]

    return retData


def createTableFive(srcData: pd.DataFrame) -> list:
    # Exact multi-indexing and level naming to use
    df5_index = [('DayOfWeek', 'M-F Afternoon'),
                 ('DayOfWeek', 'M-F Morning'),
                 ('DayOfWeek', 'S&S Afternoon'),
                 ('DayOfWeek', 'S&S Morning')]
    level_names = ['TotPeople', 'Week']

    df5 = srcData.copy()
    df5 = df5[["Week", "TimeOfActivity", "Market", "TotPeople", "ItemGroup"]]
    df5 = df5.where(df5.Market == "Market09").where(
        df5.ItemGroup == "ItemGroup2").dropna()

    df5 = df5.groupby(["Week", "TimeOfActivity"]).agg(
        {
         "TotPeople": sum
        }).reset_index()

    # pivot for activity as a column
    df5 = df5.pivot(index="Week", columns="TimeOfActivity")
    df5.columns = pd.MultiIndex.from_tuples(df5_index, names=level_names)
    df5.index.name = None
    df5 = appendGTs(df5)

    df_titles = pd.DataFrame(columns=["Market09", "ItemGroup02"])
    retData = [df_titles, df5]

    return retData


def createTableSix(srcData: pd.DataFrame) -> pd.DataFrame:
    # construct and modify df5, ie Last element (or second)
    df6 = createTableFive(srcData)[-1].copy()
    
    df6['DayOfWeek', "M-F"] = df6['DayOfWeek', "M-F Afternoon"] + df6['DayOfWeek', "M-F Morning"]
    df6['DayOfWeek', "S-S"] = df6['DayOfWeek', "S&S Afternoon"] + df6['DayOfWeek', "S&S Morning"]

    df6.drop([('DayOfWeek', 'M-F Afternoon'),
             ('DayOfWeek',   'M-F Morning'),
             ('DayOfWeek', 'S&S Afternoon'),
             ('DayOfWeek',   'S&S Morning'),
             ('', 'Grand Total')], inplace=True, axis=1)
    df6.drop(['Grand Total'], inplace=True, axis=0)

    # re calc GTs for desired cols
    df6 = appendGTs(df6)

    return df6


def createTableSeven(srcData: pd.DataFrame) -> pd.DataFrame:
    # construct and modify df6
    df6 = createTableSix(srcData).copy()
    # drop GTs, readd later
    df6.drop(['Grand Total'], inplace=True, axis=0)
    df6.drop([('', 'Grand Total')], inplace=True, axis=1)
    
    df7_avgs = df6.rolling(4).mean().drop(["2020W10", "2020W11", "2020W12"])
    
    return appendGTCol(df7_avgs)


def getTables():
    df = extract()

    l = []
    l.append(createTableOne(df))
    l.append(createTableTwo(df))
    l.extend(createTableThree(df))
    #l.extend(createTableFour(df))
    l.extend(createTableFive(df))
    l.append(createTableSix(df))
    l.append(createTableSeven(df))
    return l


def writeTables(dataList: list):
    for frame in l:
        with open('out.csv', 'a') as f:
            frame.to_csv(f)
            f.write("\n")
    return

    
