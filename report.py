__version__ = '1.1.0'
__doc__ = """Generate reports with minimal drop in!"""

# Examples with dataframes
# https://pairlist2.pair.net/pipermail/reportlab-users/2019-February/011849.html
# http://www.lucasprogramming.co.uk/pandas_07.html

# Report lab docs
# https://www.reportlab.com/docs/reportlab-userguide.pdf



# internal libs
import etl

# third party libs
import pandas as pd
import numpy as np

from reportlab.pdfgen import canvas
from reportlab.graphics import renderPDF
from reportlab.platypus import SimpleDocTemplate, Paragraph, PageBreak, KeepTogether, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm, inch

from svglib.svglib import svg2rlg

# python core
from datetime import datetime
import math
import os
import sys
from io import BytesIO

# Private vars, defaults, etc.
# opt: PAGESIZE = (140 * mm, 216 * mm) # width, height
_defaultPageSize = A4
_defaultBasemargin = 0.5 * mm
_defaultAuthor = "Albert Ferguson"
_defaultTitle = "DUMMY REPORT"
_saveDirectory = "."

# Pandas config
# Show a 20x30 grid by default and unlimit the width
pd.set_option('display.max_columns', 20)
pd.set_option('display.max_rows', 30)
pd.set_option('display.width', 100)

# Ensure large numbers are readable (round floats if any)
pd.options.display.float_format = '{:,.0f}'.format

# Set figure size for any graphs
# plt.rcParams['figure.figsize'] = (12, 10)

class BaseReport():
    def __init__(self, author=_defaultAuthor, title=_defaultTitle, pageSize=_defaultPageSize, baseMargin=_defaultBasemargin):
        ##########################################
        # PLATYPUS reportlab content control
        ##########################################

        self.sampleStyleSheet = getSampleStyleSheet()
        self.author = _defaultAuthor
        self.title = _defaultTitle
        self.pageSize = pageSize
        self.baseMargin = baseMargin
    
        # NOTE: string lit's are not rendered into the final pdf
        # Add some default content
        self.blurb = __doc__
        # Flowables hold the content of a report
        self.flowables = list()

    def __repr__(self):
        return("Report: {title} by {author}".format(title=self.title, author=self.author))

    def addDemoContent(self):
        titleStyle = self.getTitleStyle()
        bodyStyle = self.getBodyStyle()

        self.flowables.append(Paragraph(self.title, titleStyle))
        self.flowables.append(Paragraph(self.blurb, bodyStyle))
        
        return

    def buildReport(self):
        # create a byte buffer for our pdf, allows returning for multiple cases
        with BytesIO() as report_buffer:
            report_pdf = SimpleDocTemplate(
                report_buffer,
                pagesize=self.pageSize,
                topMargin=self.baseMargin,
                leftMargin=self.baseMargin,
                rightMargin=self.baseMargin,
                bottomMargin=self.baseMargin,
                title=self.title,
                author=self.author,
            )

            report_pdf.build(
                self.flowables,
                onFirstPage=self.addPageNum,
                onLaterPages=self.addPageNum
            )

            report_val = report_buffer.getvalue()
            return report_val

    def writeToPdf(self, report, fileName=_defaultTitle, fileLocation=_saveDirectory):
        filename_str = fileName + ".pdf"
        filename_path = os.path.join(_saveDirectory, filename_str)

        with open(filename_path, 'wb') as file:
            file.write(report)
        
        return

    def getBodyStyle(self):
        """
        Define styles as a function or include as a class...
        """
        style = self.sampleStyleSheet
        body_style = ParagraphStyle(
            'BodyStyle',
            fontName="Times-Roman",
            fontSize=10,
            parent=style['Heading3'],
            alignment=0,
            spaceAfter=0,
        )
        return body_style

    def getTitleStyle(self):
        """
        Define styles as a function or include as a class...
        """
        style = self.sampleStyleSheet
        title_style = ParagraphStyle(
            'TitleStyle',
            fontName="Times-Roman",
            fontSize=18,
            parent=style['Heading1'],
            alignment=1,
            spaceAfter=0,
        )
        return title_style

    ##########################################
    # Utils
    ##########################################

    def addPageNum(self, canvas, doc):
        """Page number util function for report builder."""
        canvas.saveState()
        canvas.setFont('Times-Roman', 10)
        page_num_txt = "{}".format(doc.page)
        canvas.drawCentredString(
            0.75 * inch,
            0.75 * inch,
            page_num_txt,
        )
        canvas.restoreState()

    def addText(self, canvas, doc, text: str):
        pass

    def addOverlay(self, canvas, doc):
        pass

    def addTable(self, data: pd.DataFrame, style: str, title = "Data Table"):
        """ Use pandas and reportlab together, easily ingest CSV/Excel/SQL data into dataframe format."""
        
        preTableSpacing = 20 * mm
        dataCellHeight = 6 * mm
        columnWidth = 35 * mm
        #rowHeights = len(data_list)*[dataCellHeight]
        stringMaxLength = 42

        tableHeader = Paragraph(
            "<b><font size=18>{}:</font></b>".format(title), style)

        def _strip(val: str, charLimitLen=stringMaxLength):
            return (val[:charLimitLen] + "...")
        
        t = Table(self.DataFrameToList(data), spaceBefore=preTableSpacing,
                  rowHeights=None,
                  colWidths=columnWidth,
                  repeatRows=1)

        t.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.25, colors.black),
                               ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black)]))
        
        for each in range(data.shape[0]):
            # Alternate row colouring
            if each % 2 == 0:
                bg_color = colors.whitesmoke
            else:
                bg_color = colors.lightgrey

            t.setStyle(TableStyle([('BACKGROUND', (0, each), (-1, each), bg_color)]))

        self.flowables.append(tableHeader)
        self.flowables.append(t)
        return

    def DataFrameToList(self, df: pd.DataFrame) -> list():
        headerValues_list = list()
        data_list = list()

        # also it's typical that I use multi-index, so check for that
        lvl_int = 1
        if (type(df.columns) == pd.MultiIndex):
            headerValues_list.extend([""])
            headerValues_list.extend(
                df.columns.get_level_values(lvl_int).tolist())
        else:
            headerValues_list.extend(df.columns.tolist())
            data_list = headerValues_list + \
                [list(x) for x in map(list, zip(*[df[i].values for i in df]))]
            return data_list
        
        # I usually adjust indexes anyway, typically via a grouping
        # now reportlab works row-wise, so splice the indexCol_list into the rows
        data_list.append(headerValues_list)
        for i, r in df.iterrows():
            k = [i]
            k.extend(r.tolist())
            data_list.append(k)

        return data_list


class SampleReport(BaseReport):
    def sampleTableData(self) -> list:
        return etl.getTables()

    def makeReport(self):
        print("Reading demo data...")
        demo_list_df = self.sampleTableData()

        self.addDemoContent();
        tableStyling = self.getBodyStyle()
        print("Adding tables...")
        
        i = 1
        for df in demo_list_df:
            if (df.shape[0] != 0):
                self.addTable(df[:25], tableStyling, "Table: {}".format(i))
            i += 1

        print("Building and writing the report...")
        self.writeToPdf(self.buildReport())
        print("Done!")
        return
