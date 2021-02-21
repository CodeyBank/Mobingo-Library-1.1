import sys
import platform
import pymysql
import pyautogui as sc
import datetime, time, random, string, json
from PyQt5.uic import loadUiType
from PyQt5 import QtCore
from PyQt5.QtCore import (QCoreApplication, QPropertyAnimation, QDate, QDateTime, QMetaObject, QObject, QPoint, QRect,
                          QSize, QTime, QUrl, Qt, QEvent, QTimer)
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.Qt import Qt
from PyQt5.QtGui import QPainter, QPen, QFont, QColor
from PyQt5.QtChart import QChart, QChartView, QBarSet, QPercentBarSeries, QBarCategoryAxis, QBarSet, QValueAxis, \
    QBarSeries, QPieSeries, QPieSlice

pymysql.install_as_MySQLdb()
import MySQLdb

from xlrd import *
from xlsxwriter import *

mainApp, _ = loadUiType('library.ui')
loginApp, _ = loadUiType('login.ui')
registerApp, _ = loadUiType('register.ui')
newOpsApp, _ = loadUiType('newOperation.ui')
modifyOpsApp, _ = loadUiType('modifyOperation.ui')
progress, _ = loadUiType('progressBar.ui')

# GLOBALS
counter = 0
jumper = 20


def showDialog(error_type, text, message):
    msg = QMessageBox()
    if error_type == 'information':
        msg.setIcon(QMessageBox.Information)
    if error_type == 'error':
        msg.setIcon(QMessageBox.Warning)
    msg.setText(text)
    msg.setInformativeText(message)
    msg.setWindowTitle("Information")
    msg.setStandardButtons(QMessageBox.Ok)
    retVal = msg.exec_()
    if retVal == QMessageBox.Ok:
        # self.closeWindow()
        pass


class MainWindow(QMainWindow, mainApp):
    currentUser = ''

    def __init__(self, parent=None):
        QMainWindow.__init__(self)
        self.setupUi(self)

        # Instantiate method to handle all button clicks
        self.buttonHandler()

        # Set initial window size
        startSize = QSize(1600, 800)
        self.resize(startSize)
        self.setMinimumSize(startSize)

        # Connect to the database
        self.db = MySQLdb.connect(host='localhost', user='root', password='Thebossm@#995', db="library", port=3310)
        self.cur = self.db.cursor()

        # Adjust table widgets
        self.adjustTableWidget()
        self.resize_tHeaders()
        self.sideBar.setMaximumWidth(60)

        self.bookPiePlot()
        self.clientPiePlot()
        self.clientCatPlot()
        self.plotClientData()

        # Toggle side menu size
        self.toggleButton.clicked.connect(lambda: self.toggleMenu(220, True))

        # Set the default screen
        self.selectStandardMenu("dashBoardBtn")
        self.stackedWidget.setCurrentWidget(self.dashBoardPage)

        # Populate table data
        self.show_all_operations()
        self.showAllBooks()
        self.plotBookData()

        # Create and Activate timer
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.updateTime)
        self.timer.start()
        self.themesSettings()

    def toggleMenu(self, maxWidth, enable):
        if enable:
            # GET WIDTH
            width = self.sideBar.width()

            # SET MAX WIDTH
            if width == 60:
                widthToExtend = maxWidth
            else:
                widthToExtend = 60
            # ANIMATION
            self.animation = QPropertyAnimation(self.sideBar, b"minimumWidth")
            self.animation.setDuration(300)
            self.animation.setStartValue(width)
            self.animation.setEndValue(widthToExtend)
            self.animation.setEasingCurve(QtCore.QEasingCurve.InOutQuart)
            self.animation.start()

    def logOut(self):
        self.loginWin = loginWindow()
        self.close()
        self.loginWin.show()

    def buttonHandler(self):
        # this handles filters on the dashboard table
        self.transactionFilter.clicked.connect(lambda: self.filterOperations('transaction_id', 'trID'))
        self.usernameFiler.clicked.connect(lambda: self.filterOperations('username', 'uName'))
        self.bookTitleFIlter.clicked.connect(lambda: self.filterOperations('client', 'clName'))
        self.clearFilterBtn.clicked.connect(self.show_all_operations)

        # Tool buttons on the operations and books table
        self.editOpBtn.clicked.connect(self.openModifyOperation)
        self.addUserBtn_3.clicked.connect(self.addBooks)
        self.pushButton_8.clicked.connect(self.searchBooks)
        self.pushButton_6.clicked.connect(self.updateBooks)
        self.pushButton_7.clicked.connect(self.deleteBooks)
        self.exportBtn.clicked.connect(self.exportOperations)

        # Navigation buttons on the side menu
        self.dashBoardBtn.clicked.connect(self.navigationButtons)
        self.dashBoardBtn.clicked.connect(self.updateDataLabels)
        self.booksButton.clicked.connect(self.navigationButtons)
        self.usersBtn.clicked.connect(self.navigationButtons)
        self.settingsBtn.clicked.connect(self.navigationButtons)

        self.statisticsBtn.clicked.connect(self.navigationButtons)
        self.statisticsBtn.clicked.connect(self.plotBookData)
        self.statisticsBtn.clicked.connect(self.updateDataLabels)
        self.statisticsBtn.clicked.connect(self.plotClientData)
        self.statisticsBtn.clicked.connect(self.clientCatPlot)
        self.statisticsBtn.clicked.connect(self.clientPiePlot)

        # Logout button
        self.logOutBtn.clicked.connect(self.logOut)
        # Popup windows
        self.addNewOpBtn.clicked.connect(self.addNewOps)
        # Users page
        self.addClientBtn.clicked.connect(self.addNewClient)
        self.clientSearch.clicked.connect(self.searchClient)
        self.editClient.clicked.connect(self.editClientDetails)

        # Settings Page
        self.applySettingsBtn.clicked.connect(self.configuration)

        # Books filter buttons
        self.bookIDFilterBtn.clicked.connect(lambda: self.filterBooks("book_code", "bookID"))
        self.titleFilterBtn.clicked.connect(lambda: self.filterBooks("book_title", "title"))
        self.authorFilterBtn.clicked.connect(lambda: self.filterBooks("book_author", "author"))
        self.searchOpBtn_2.clicked.connect(self.showAllBooks)
        self.editOpBtn_2.clicked.connect(lambda: self.tabWidget.setCurrentIndex(1))
        self.exportBtn_2.clicked.connect(self.exportBooks)

    def adjustTableWidget(self):
        self.tableWidget.horizontalHeader().setVisible(True)
        self.tableWidget.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.tableWidget_2.horizontalHeader().setVisible(True)
        self.tableWidget_2.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)

    def resize_tHeaders(self):
        t1 = range(0, 9)
        t2 = range(0, 8)
        header_ops = self.tableWidget_2.horizontalHeader()
        header_allbooks = self.tableWidget.horizontalHeader()

        for item in t1:
            header_ops.setSectionResizeMode(item, QtWidgets.QHeaderView.ResizeToContents)
        for item1 in t2:
            header_allbooks.setSectionResizeMode(item1, QtWidgets.QHeaderView.ResizeToContents)

    def selectStandardMenu(self, widget):
        for w in self.top_Buttons.findChildren(QPushButton):
            if w.objectName() == widget:
                w.setStyleSheet(self.selectMenu(w.styleSheet()))

    ## ==> RESET SELECTION
    def resetStyle(self, widget):
        # search for all the objects (children) in the parent object
        for w in self.top_Buttons.findChildren(QPushButton):
            if w.objectName() != widget:
                w.setStyleSheet(self.deselectMenu(w.styleSheet()))

    @staticmethod
    def selectMenu(getStyle):
        select = getStyle + ("""
        QPushButton {
        background-position: left;
        background-repeat: no-repeat;
        border: none;
        border-left: 20px solid rgba(107, 112, 141, 10);
        background-color: rgb(107, 112, 141);
        text-align: left;
        padding-left: 60px;
        color:white;}""")
        return select

    ## ==> DESELECT
    @staticmethod
    def deselectMenu(getStyle):
        deselect = getStyle.replace(("""
        QPushButton {
        background-position: left;
        background-repeat: no-repeat;
        border: none;
        border-left: 20px solid rgba(107, 112, 141, 10);
        background-color: rgb(107, 112, 141);
        text-align: left;
        padding-left: 60px;
        color:white;}"""), "")
        return deselect

    def addNewOps(self):
        self.window4 = addNewOperation()
        self.window4.show()

    def navigationButtons(self):
        btnWidget = self.sender()
        if btnWidget.objectName() == 'dashBoardBtn':
            self.stackedWidget.setCurrentWidget(self.dashBoardPage)
            self.resetStyle('dashBoardBtn')
            btnWidget.setStyleSheet(self.selectMenu(btnWidget.styleSheet()))
        if btnWidget.objectName() == 'booksButton':
            self.stackedWidget.setCurrentWidget(self.booksPage)
            self.resetStyle('booksButton')
            btnWidget.setStyleSheet(self.selectMenu(btnWidget.styleSheet()))
        if btnWidget.objectName() == 'usersBtn':
            self.stackedWidget.setCurrentWidget(self.usersPage)
            self.resetStyle('usersBtn')
            btnWidget.setStyleSheet(self.selectMenu(btnWidget.styleSheet()))
        if btnWidget.objectName() == 'settingsBtn':
            self.stackedWidget.setCurrentWidget(self.settingsPage)
            self.resetStyle('settingsBtn')
            btnWidget.setStyleSheet(self.selectMenu(btnWidget.styleSheet()))
        if btnWidget.objectName() == 'statisticsBtn':
            self.stackedWidget.setCurrentWidget(self.statisticsPage)
            self.resetStyle('statisticsBtn')
            btnWidget.setStyleSheet(self.selectMenu(btnWidget.styleSheet()))

    def show_all_operations(self):

        self.tableWidget_2.setRowCount(0)
        self.tableWidget_2.insertRow(0)
        self.cur.execute('''
              SELECT * FROM operations
              ''')
        data = self.cur.fetchall()
        if data:
            for row, form in enumerate(data):
                for column, item in enumerate(form):
                    self.tableWidget_2.setItem(row, column, QTableWidgetItem(str(item)))
                current_row = self.tableWidget_2.rowCount()
                self.tableWidget_2.insertRow(current_row)
        self.updateDataLabels()

    # Get the number of books burrowed in the day
    def countValues(self, activityType, dop):
        self.db = MySQLdb.connect(host='localhost', user='root', password='Thebossm@#995', db="library", port=3310)
        self.cur = self.db.cursor()
        sql = """SELECT count(opsdate) FROM library.operations where opsdate = '{dateval}' and activity = '{val}'"""
        sql = sql.replace("{dateval}", dop).replace("{val}", activityType)
        self.cur.execute(sql)
        returnVal = self.cur.fetchone()[0]
        return returnVal

    def updateDataLabels(self):
        self.cur.execute("SELECT count(DISTINCT book_code) from library.book")
        numberOfBooks = self.cur.fetchone()[0]
        self.cur.execute("SELECT count(idusers) from library.users")
        numberOfUsers = self.cur.fetchone()[0]
        self.cur.execute("SELECT count(*) from library.clients")
        numberOfClients = self.cur.fetchone()[0]
        self.cur.execute("SELECT count(*) from library.operations")
        operations = self.cur.fetchone()[0]

        tD = str(datetime.date.today())
        numberOfBurrowedBooks = self.countValues("Burrow", tD)
        numberOfBooksBought = self.countValues("Buy", tD)
        numberInLibrary = self.countValues("Use In Library", tD)
        numberReturned = self.countValues("Return", tD)

        # Get the source text of the label and save in a variable
        # ---- On the Dashboard page ------------------------------------------------------------------
        dbBooksAvailLbl = self.dbBooksAvailable.text().replace("{value}", str(numberOfBooks))
        dbInLibraryLbl = self.dbInLibrary.text().replace("{value}", str(numberInLibrary))
        dbBurrowedBooksLbl = self.dbBooksBurrowed.text().replace("{value}", str(numberOfBurrowedBooks))
        dbBooksSoldLbl = self.dbBooksSold.text().replace("{value}", str(numberOfBooksBought))
        dbBooksReturnedLbl = self.dbReturned.text().replace("{value}", str(numberReturned))

        # Update the UI on Dashboard Page
        self.dbBooksAvailable.setText(dbBooksAvailLbl)
        self.dbInLibrary.setText(dbInLibraryLbl)
        self.dbBooksBurrowed.setText(dbBurrowedBooksLbl)
        self.dbBooksSold.setText(dbBooksSoldLbl)
        self.dbReturned.setText(dbBooksReturnedLbl)

        # -------------------------------------------------------------------------------------------------------------
        # Update UI on the Books page
        lblBooks = self.abAvailableBooks.text().replace("{value}", str(numberOfBooks))
        self.abAvailableBooks.setText(lblBooks)
        # ------------------------------------------------------------------------------------------------------------

        # ---- On the Statistics Page --------------------------------------------------------------------------------
        # Replace the font sizes
        stBooksAvailLbl = dbBooksAvailLbl.replace('36pt', '15pt').replace('14pt', '10pt')
        stBooksBurrLbl = dbBurrowedBooksLbl.replace('36pt', '15pt').replace('14pt', '10pt')
        stBooksSoldLbl = dbBooksSoldLbl.replace('36pt', '15pt').replace('14pt', '10pt')
        stBooksReturnedLbl = dbBooksReturnedLbl.replace('36pt', '15pt').replace('14pt', '10pt')

        registeredClientsLbl = self.stClients.text().replace('{value}', str(numberOfClients))
        registeredUsersLbl = self.stUsers.text().replace('{value}', str(numberOfUsers))
        totalOperationsLbl = self.stOperations.text().replace('{value}', str(operations))

        # Update the UI on Statistics Page
        self.stBooksAvail.setText(stBooksAvailLbl)
        self.stBurrowedBooks.setText(stBooksBurrLbl)
        self.stBooksSold.setText(stBooksSoldLbl)
        self.stBooksReturned.setText(stBooksReturnedLbl)

        self.stOperations.setText(totalOperationsLbl)
        self.stUsers.setText(registeredUsersLbl)
        self.stClients.setText(registeredClientsLbl)

    # Handle error message boxes
    @staticmethod
    def showDialog(error_type='a', text='b', message='c'):
        msg = QMessageBox()
        if error_type == 'information':
            msg.setIcon(QMessageBox.Information)
        if error_type == 'error':
            msg.setIcon(QMessageBox.Warning)
        msg.setText(text)
        msg.setInformativeText(message)
        msg.setWindowTitle("Information")
        msg.setStandardButtons(QMessageBox.Ok)
        retVal = msg.exec_()
        if retVal == QMessageBox.Ok:
            pass

    def filterOperations(self, querytype, queryValue):
        # Retrieve user inputs
        tID = self.filterTransaction.text()
        userName = self.filterBookTitle.text()
        clientName = self.filterClientName.text()
        self.tableWidget_2.setRowCount(0)
        self.tableWidget_2.insertRow(0)
        sql = ''' SELECT * FROM operations WHERE #column = "#value" '''
        if queryValue == 'trID':
            s1 = sql.replace('#column', querytype).replace("#value", tID)
            self.cur.execute(s1)
        elif queryValue == 'uName':
            s1 = sql.replace('#column', querytype).replace("#value", userName)
            self.cur.execute(s1)
        elif queryValue == 'clName':
            s1 = sql.replace('#column', querytype).replace("#value", clientName)
            self.cur.execute(s1)
        else:
            pass
            # self.statusBar().showMessage("Fields cannot be empty", 3000)

        data = self.cur.fetchall()
        if data:
            for row, form in enumerate(data):
                for column, item in enumerate(form):
                    self.tableWidget_2.setItem(row, column, QTableWidgetItem(str(item)))
                current_row = self.tableWidget_2.rowCount()
                self.tableWidget_2.insertRow(current_row)
        else:
            self.statusBar.showMessage("No records found", 3000)

    def filterBooks(self, querytype, queryValue):
        # Retrieve user inputs
        bookID = self.filterBookID.text()
        bookTitle = self.filterBookTitle_3.text()
        bookAuthor = self.filterAuthor.text()

        self.tableWidget.setRowCount(0)
        self.tableWidget.insertRow(0)

        sql = ''' SELECT * FROM book WHERE #column = "#value" '''
        if queryValue == 'bookID':
            s1 = sql.replace('#column', querytype).replace("#value", bookID)
            self.cur.execute(s1)
        elif queryValue == 'title':
            s1 = sql.replace('#column', querytype).replace("#value", bookTitle)
            self.cur.execute(s1)
        elif queryValue == 'author':
            s1 = sql.replace('#column', querytype).replace("#value", bookAuthor)
            self.cur.execute(s1)
        else:
            self.statusBar.showMessage("Fields cannot be empty", 3000)

        data = self.cur.fetchall()

        if data:
            for row, form in enumerate(data):
                for column, item in enumerate(form):
                    self.tableWidget.setItem(row, column, QTableWidgetItem(str(item)))
                current_row = self.tableWidget.rowCount()
                self.tableWidget.insertRow(current_row)
        else:
            self.statusBar.showMessage("No records found", 3000)

    def exportOperations(self):
        # Request user storage location
        fileName = QFileDialog.getSaveFileUrl(self, 'Save File', QUrl('c:\\Library_operations'),
                                              "Microsoft Excel (*.xlsx)")
        fileName = fileName[0].toString()[8:]
        if fileName:
            self.cur.execute('''SELECT * FROM operations''')
            data = self.cur.fetchall()
            # create a new excel workbook
            wb = Workbook(fileName)
            # create a new sheet in the workbook to store data
            sheet_1 = wb.add_worksheet("Today's Ops Data")

            # Create columns and give them names
            sheet_1.write(0, 0, 'Transaction ID')
            sheet_1.write(0, 1, 'Client Name')
            sheet_1.write(0, 2, 'Username')
            sheet_1.write(0, 3, 'Book ID')
            sheet_1.write(0, 4, 'Activity')
            sheet_1.write(0, 5, 'Date of Operation')
            sheet_1.write(0, 6, 'Time of Operation')
            sheet_1.write(0, 7, 'Expected Return Date')
            sheet_1.write(0, 5, 'Remarks')

            # write data in the created columns using a nested for
            row_number = 1  # remember row 1 has already been used for the column headers
            for row in data:
                column_number = 0  # Each time this loop is iterated start at the first column
                for item in row:
                    sheet_1.write(row_number, column_number, str(item))
                    column_number += 1  # increase the column number for each line of entry
                row_number += 1  # add data to the next row after each iteration of the loop is completed

            wb.close()  # book must be closed
            self.showDialog('information', 'Operation Successful', "File exported successfully")

    def exportBooks(self):
        # Request user storage location
        fileName = QFileDialog.getSaveFileUrl(self, 'Save File', QUrl('c:\\Books'),
                                              "Microsoft Excel (*.xlsx)")
        fileName = fileName[0].toString()[8:]
        if fileName:
            self.cur.execute('''SELECT * FROM book''')
            data = self.cur.fetchall()
            # create a new excel workbook
            wb = Workbook(fileName)
            # create a new sheet in the workbook to store data
            sheet_1 = wb.add_worksheet("Books")

            # Create columns and give them names
            sheet_1.write(0, 0, 'SN')
            sheet_1.write(0, 1, 'ISBN')
            sheet_1.write(0, 2, 'Title')
            sheet_1.write(0, 3, 'Author')
            sheet_1.write(0, 4, 'Category')
            sheet_1.write(0, 5, 'Publisher')
            sheet_1.write(0, 6, 'Price')
            sheet_1.write(0, 7, 'Location')
            sheet_1.write(0, 5, 'Description')

            # write data in the created columns using a nested for
            row_number = 1  # remember row 1 has already been used for the column headers
            for row in data:
                column_number = 0  # Each time this loop is iterated start at the first column
                for item in row:
                    sheet_1.write(row_number, column_number, str(item))
                    column_number += 1  # increase the column number for each line of entry
                row_number += 1  # add data to the next row after each iteration of the loop is completed

            wb.close()  # book must be closed
            self.showDialog('information', 'Operation Successful', "File exported successfully")

    def updateTime(self):
        toDay = datetime.datetime.today()
        dt_string = toDay.strftime("%A %d %B, %Y %I:%M %p")
        self.dateTime.setText(dt_string)

    def openModifyOperation(self):
        self.window3 = modifyOperation()
        self.window3.show()

    def showAllBooks(self):
        self.tableWidget.setRowCount(0)
        self.tableWidget.insertRow(0)
        self.cur.execute('''
                      SELECT * FROM book
                      ''')
        data = self.cur.fetchall()
        if data:
            for row, form in enumerate(data):
                for column, item in enumerate(form):
                    self.tableWidget.setItem(row, column, QTableWidgetItem(str(item)))
                current_row = self.tableWidget.rowCount()
                self.tableWidget.insertRow(current_row)

    def addBooks(self):
        title = self.bookTitleLE.text()
        author = self.authorLE.text()
        publisher = self.publisherLE.text()
        book_id = self.isbnLE.text()
        category = self.categoryLE.currentText()
        cost = self.yearpubLE_3.text()
        location = self.yearpubLE_2.text()
        description = self.textEdit.toPlainText()
        sql = '''INSERT INTO book
                (book_code, book_title, book_author,
                 book_category, book_publisher, book_price,
                 location, book_description) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)'''
        self.cur.execute(sql, (book_id, title, author, category, publisher, cost, location, description))
        self.db.commit()
        self.showDialog("Information","Successful", "Book added successfully")
        self.showAllBooks()
        self.updateDataLabels()
        self.plotBookData()
        self.statusBar.showMessage('Book added Successfully', 3000)

    def searchBooks(self):
        global query
        query = self.lineEdit.text()
        self.cur.execute("SELECT * FROM book WHERE book_title = %s", query)
        data = self.cur.fetchone()

        if data:
            self.statusBar.showMessage('Record found', 3000)
            self.bookTitleLE_2.setText(data[2])
            self.authorLE_2.setText(data[3])
            self.publisherLE_2.setText(data[5])
            self.isbnLE_2.setText(data[1])
            self.categoryLE_2.setCurrentText(data[4])
            self.yearpubLE_4.setText(data[7])
            self.yearpubLE_5.setText(str(data[6]))
            self.textEdit_2.setPlainText(data[8])
        else:
            self.statusBar.showMessage('Record not found', 3000)

    def updateBooks(self):
        title = self.bookTitleLE_2.text()
        author = self.authorLE_2.text()
        publisher = self.publisherLE_2.text()
        book_id = self.isbnLE_2.text()
        category = self.categoryLE_2.currentText()
        location = self.yearpubLE_4.text()
        price = self.yearpubLE_5.text()
        description = self.textEdit_2.toPlainText()
        sql = """UPDATE book SET
                book_code = %s,
                book_title = %s,
                book_author = %s,
                book_category = %s,
                book_publisher = %s,
                book_price = %s,
                location = %s,
                book_description = %s
                WHERE book_code = %s
              """
        self.cur.execute(sql, (book_id, title, author, category, publisher, price, location, description, book_id))
        self.statusBar.showMessage('Record updated successfully', 3000)
        self.showAllBooks()

    def deleteBooks(self):

        warning = QMessageBox.warning(self, "Delete Book", "Are you sure you want to delete this book?",
                                      QMessageBox.Yes | QMessageBox.No)
        if warning == QMessageBox.Yes:
            sql = """DELETE FROM book WHERE book_code=%s"""
            self.cur.execute(sql, query)
            self.db.commit()
            self.showAllBooks()
            self.statusBar.showMessage("Book deleted successfully", 3000)

    def addNewUser(self):
        first_name = self.firstNameLE_2.text()
        last_name = self.lastNameLE_2.text()
        username = self.userNameLE_2.text()
        email = self.emailLE_2.text()
        password = self.passwordLE_2.text()
        repeatPassword = self.repeatPasswordLE_2.text()
        type = self.comboBox_6.currentText()

        # parse password and email through authentication function
        result = self.credentialAuth(p=password, rp=repeatPassword, em=email)
        print(result)
        if not result[0] and not result[1]:
            sql = """INSERT into users
                    (fname, lname, user_name, user_email, user_password, type)
                    VALUES (%s, %s, %s, %s, %s, %s)
                  """
            self.cur.execute(sql, (first_name, last_name, username, email, password, type))
            self.db.commit()
            self.statusBar.showMessage('User added Successfully', 3000)

    def searchClient(self):
        id = self.idNumber.text()
        self.cur.execute("SELECT * FROM clients WHERE idclients = %s", id)
        data = self.cur.fetchone()

        if data:
            self.fname.setText(data[1])
            self.surname.setText(data[2])
            self.emailLE_5.setText(data[3])
            self.gender.setCurrentText(data[4])
            self.address_2.setText(data[5])
            self.age.setValue(data[6])
            self.occupation.setCurrentText(data[7])

        else:
            self.showDialog("error", "Error: Client not found")

    def addNewClient(self):
        first_name = self.firstNameLE_4.text()
        last_name = self.firstNameLE_5.text()
        gender = self.genderCB.currentText()
        email = self.emailLE.text()
        age = self.clientAge.value()
        address = self.address.text()
        id = self.idNumber.text()
        occupation = self.occuptationCB.currentText()

        self.cur.execute("SELECT * FROM clients WHERE idclients = %s", id)
        data = self.cur.fetchone()

        if data:
            self.showDialog("error", "Invalid ID number", "ID Number already exists in the database")
        else:
            sql = """INSERT into clients
                    (idclients, first_name, surname, client_email, gender, address, age, occupation)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                  """
            self.cur.execute(sql, (id, first_name, last_name, email, gender, address, age, occupation))
            self.db.commit()
            self.showDialog("information", "Operation successful", "Client added successfully")

    def editClientDetails(self):
        first_name = self.firstNameLE_4.text()
        last_name = self.firstNameLE_5.text()
        gender = self.genderCB.currentText()
        email = self.emailLE.text()
        age = self.clientAge.value()
        address = self.address.text()
        id = self.idNumber.text()
        occupation = self.occuptationCB.currentText()

        # load data into database
        sql = """INSERT into clients
                (idclients, first_name, surname, client_email, gender, address, age, occupation)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
              """
        self.cur.execute(sql, (id, first_name, last_name, email, gender, address, age, occupation))
        self.db.commit()
        self.showDialog("information", "Operation successful", "Client added successfully")

    def credentialAuth(self, **kwargs):
        _password = kwargs['p']
        _repeatPassword = kwargs['rp']
        _email = kwargs['em']

        specialCharacters = ["@", '#', '$', '%', '^', '&', '(', ')', '-', "=", "+", '<', '>']
        errorFlag = False
        check = []
        print(_password, _repeatPassword, _email)

        if _password != _repeatPassword:
            errorFlag = True
            self.statusBar.showMessage('Passwords do not match', 3000)

        if len(_password) < 5:
            errorFlag = True
            self.statusBar.showMessage('Password too short', 3000)
        # confirm that there is a special character in the password
        for character in specialCharacters:
            if character not in _password:
                check.append('N')
                # print('special character not found')
            else:
                check.append('Y')
        if 'Y' not in check:
            errorFlag = True
            self.statusBar.showMessage('Password must contain special characters', 3000)

        if (_password == '') and (_repeatPassword == ''):
            errorFlag = True
            self.statusBar.showMessage('Password fields cannot be empty', 3000)

        errorFlagEM = False

        for character in _email:
            if '@' not in _email:
                self.statusBar.showMessage('Invalid Email address', 3000)
                errorFlagEM = True

        return errorFlagEM, errorFlag

    def modifyUser(self):
        username = self.lineEdit_27.text()
        password = self.lineEdit_28.text()
        sql = '''SELECT * FROM users '''
        self.cur.execute(sql)
        data = self.cur.fetchall()
        for row in data:
            if username == row[3] and password == row[5]:
                self.statusBar.showMessage('User account found', 3000)
                self.groupBox_3.setEnabled(True)
                self.lineEdit_21.setText(row[1])
                self.lineEdit_22.setText(row[2])
                self.lineEdit_23.setText(row[3])
                self.lineEdit_24.setText(row[4])
                self.lineEdit_25.setText(row[5])
                self.comboBox_3.setCurrentText(row[6])
            else:
                self.groupBox_3.setEnabled(False)
                self.statusBar.showMessage('Invalid credentials, please try again', 3000)

    def updateUser(self):
        firstName = self.lineEdit_21.text()
        lastName = self.lineEdit_22.text()
        userName = self.lineEdit_23.text()
        password = self.lineEdit_24.text()
        email = self.lineEdit_25.text()
        opType = self.comboBox_3.currentText()
        sql = '''UPDATE users SET
                 fname = %s,
                 lname = %s,
                 user_name = %s,
                 user_email = %s,
                 user_password = %s,
                 type = %s
                 WHERE user_name = %s
        '''
        self.cur.execute(sql, (firstName, lastName, userName, email, password, opType, userName))
        self.db.commit()
        self.statusBar.showMessage('User details modified successfully', 3000)

    # These methods pertain to the settings page
    def configuration(self):
        configFile = open("config.json", "w")

        details = {"dbConfig": {
                        "username": "default",
                        "password": "",
                        "port": "8080"},
                   "fonts": {
                        "fontFamily": "default",
                        "fontSize": "15"
                   },
                   "selectedTheme": "default",
                   "notification": {
                        "allowNotif": "False",
                        "TurnoffNotif": "False",
                        "logNotifications": "False"
                   },
                   "Initiator": "Default",
                   "targetUser": "Default",
                   "UserPrivileges": {
                         "changeTheme": "False",
                         "viewStatistics": "False",
                         "configDB": "False",
                         "addUser": "False",
                         "removeUser": "False",
                         "addOperation": "False"
                   }
        }

        details["dbConfig"]["username"] = self.lineEdit_11.text()
        details["dbConfig"]["password"] = self.lineEdit_13.text()
        details["dbConfig"]["port"] = self.lineEdit_14.text()
        details["fonts"]["fontFamily"] = self.fontComboBox.currentText()
        details["fonts"]["fontSize"] = self.comboBox_4.currentText()

        if self.radioButton.isChecked():
            details["selectedTheme"] = self.radioButton.text()
        if self.radioButton_2.isChecked():
            details["selectedTheme"] = self.radioButton_2.text()
        if self.radioButton_3.isChecked():
            details["selectedTheme"] = self.radioButton_3.text()

        if self.changeThemeCB.isChecked():
            details["notification"]["changeTheme"] = "True"
        if self.veiwStatisticsChB_2.isChecked():
            details['notification']['viewStatistics'] = "True"
        if self.configDBChB.isChecked():
            details['notification']['configDB'] = "True"
        if self.addUserCB.isChecked():
            details["UserPrivileges"]["addUser"] = "True"
        if self.RemoveUserChB.isChecked():
            details['UserPrivileges']['removeUser'] = "True"
        if self.veiwStatisticsChB.isChecked():
            details['UserPrivileges']['addOperation'] = "True"

        details["Initiator"] = self.currentUser
        details["targetUser"] = self.userComboList.currentText()

        # covert details to json and write to config file
        detailsJson = json.dumps(details, indent=4, sort_keys=True)
        configFile.write(detailsJson)
        configFile.close()
        self.showDialog("information", "Configuration Saved Successfully", "Changes will be effected after restart")
        self.themesSettings()

    def themesSettings(self):

        global configFile
        try:
            configFile = open("config.json", mode='r', encoding='utf-8')
            settings = json.loads(configFile.read())
            print(settings["selectedTheme"])
            if settings["selectedTheme"] == 'Theme 1':
                style = open('themes/demo.css', 'r')
                style = style.read()
                self.setStyleSheet(style)

            if settings["selectedTheme"] == 'Theme 2':
                style = open('themes/ConsoleStyle.css', 'r')
                style = style.read()
                self.setStyleSheet(style)

            if settings["selectedTheme"] == 'Theme 3':
                style = open('themes/MaterialDark.css', 'r')
                style = style.read()
                self.setStyleSheet(style)
        finally:
            configFile.close()

    # These functions control the statistics page
    def bookPiePlot(self):
        # Perform SQL queries
        self.cur.execute('SELECT count(book_category) from library.book where book_category = "Literature"')
        literature = self.cur.fetchone()
        self.cur.execute('SELECT count(book_category) from library.book where book_category = "Science and Technology"')
        sci_tech = self.cur.fetchone()
        self.cur.execute('SELECT count(book_category) from library.book where book_category = "Art"')
        arts = self.cur.fetchone()
        self.cur.execute('SELECT count(book_category) from library.book where book_category = "International Politics"')
        int_pol = self.cur.fetchone()

        # Create Pies series object
        series = QPieSeries()
        series.setHoleSize(0.35)
        series.append("Literature", literature[0])
        series.append("Science and Tech", sci_tech[0])
        series.append("Arts", arts[0])
        series.append("International Politics", int_pol[0])
        series.setLabelsVisible(True)

        series.setLabelsPosition(QPieSlice.LabelOutside)
        for slice1 in series.slices():
            slice1.setLabel("{:.2f}%".format(100 * slice1.percentage()))

        chart = QChart()
        chart.addSeries(series)
        chart.createDefaultAxes()
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignRight)

        # Set markers for the legend
        chart.legend().markers(series)[0].setLabel("Literature")
        chart.legend().markers(series)[1].setLabel("Science and Tech")
        chart.legend().markers(series)[2].setLabel("Arts")
        chart.legend().markers(series)[3].setLabel("International Politics")

        # Instantiate chartview class
        chartview = QChartView(chart)
        chartview.setRenderHint(QPainter.Antialiasing)

        # Clear margins of the widget and assign chart to widget
        self.bookCatPie.setContentsMargins(0, 0, 0, 0)
        lay1 = QtWidgets.QHBoxLayout(self.bookCatPie)
        lay1.setContentsMargins(0, 0, 0, 0)
        lay1.addWidget(chartview)

    def plotBookData(self):
        todayDate = datetime.date.today()
        lastSevenDays = list(map(lambda x: str(todayDate - datetime.timedelta(days=x)), range(0, 7)))
        noOfBurrowedBooks = [self.countValues("Burrow", _) for _ in lastSevenDays]
        noOfBooksSold = [self.countValues("Buy", _) for _ in lastSevenDays]
        noOfReturns = [self.countValues("Return", _) for _ in lastSevenDays]
        useInLibrary = [self.countValues("Use in Library", _) for _ in lastSevenDays]
        rangeVal = noOfBooksSold + noOfBurrowedBooks + noOfReturns + useInLibrary

        # Create the barset
        set0 = QBarSet('Burrowed')
        set1 = QBarSet('Sold')
        set2 = QBarSet('Returned')
        set3 = QBarSet('In Library use')

        set0.append(noOfBurrowedBooks)
        set1.append(noOfBooksSold)
        set2.append(useInLibrary)
        set3.append(noOfReturns)

        series = QBarSeries()
        series.append(set0)
        series.append(set1)
        series.append(set2)
        series.append(set3)

        chart = QChart()
        chart.addSeries(series)
        # chart.setTitle("Books Burrowed in 7 days")
        chart.setAnimationOptions(QChart.SeriesAnimations)

        axisX = QBarCategoryAxis()
        axisX.append([(str(_[8:]) + 'th') for _ in lastSevenDays])
        axisY = QValueAxis()
        axisY.setRange(0, max(rangeVal))

        chart.addAxis(axisX, Qt.AlignBottom)
        chart.addAxis(axisY, Qt.AlignLeft)

        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignTop)

        chartView = QChartView(chart)
        chartView.setRenderHint(QPainter.Antialiasing)

        self.burrowedBooksPlot.setContentsMargins(0, 0, 0, 0)

        lay1 = QtWidgets.QVBoxLayout(self.burrowedBooksPlot)
        lay1.setContentsMargins(0, 0, 0, 0)
        lay1.addWidget(chartView)

    def clientPiePlot(self):
        # Perform SQL queries
        self.cur.execute('SELECT count(gender) from library.clients where gender = "Male"')
        male = self.cur.fetchone()
        self.cur.execute('SELECT count(gender) from library.clients where gender = "Female"')
        female = self.cur.fetchone()

        # Create Pies series object
        series = QPieSeries()
        # series.setHoleSize(0.35)
        series.append("Male", male[0])
        series.append("Female", female[0])
        series.setLabelsVisible(True)

        series.setLabelsPosition(QPieSlice.LabelOutside)
        for slice1 in series.slices():
            slice1.setLabel("{:.2f}%".format(100 * slice1.percentage()))

        chart = QChart()
        chart.addSeries(series)
        chart.createDefaultAxes()
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignTop)

        # Set markers for the legend
        chart.legend().markers(series)[0].setLabel("Male")
        chart.legend().markers(series)[1].setLabel("Female")

        # Instantiate chartview class
        chartview = QChartView(chart)
        chartview.setRenderHint(QPainter.Antialiasing)

        # Clear margins of the widget and assign chart to widget
        self.pieChart.setContentsMargins(0, 0, 0, 0)
        lay1 = QtWidgets.QHBoxLayout(self.pieChart)
        lay1.setContentsMargins(0, 0, 0, 0)
        lay1.addWidget(chartview)

    def clientCatPlot(self):
        # Perform SQL queries
        self.cur.execute('SELECT count(occupation) from library.clients where occupation = "Engineer"')
        engineer = self.cur.fetchone()
        self.cur.execute('SELECT count(gender) from library.clients where gender = "Medic"')
        medics = self.cur.fetchone()
        self.cur.execute('SELECT count(gender) from library.clients where gender = "Carpenter"')
        carpenter = self.cur.fetchone()
        self.cur.execute('SELECT count(gender) from library.clients where gender = "Crafts-man"')
        crafts_man = self.cur.fetchone()
        self.cur.execute('SELECT count(gender) from library.clients where gender = "Lawyer"')
        lawyer = self.cur.fetchone()
        self.cur.execute('SELECT count(gender) from library.clients where gender = "Self-employed"')
        selfEmployed = self.cur.fetchone()
        self.cur.execute('SELECT count(*) from library.clients ')
        totalClients = self.cur.fetchone()

        # Create Pies series object
        series = QPieSeries()
        series.setHoleSize(0.3)
        series.append("Engineer", engineer[0])
        series.append("Medic", medics[0])
        series.append("Carpenter", carpenter[0])
        series.append("Crafts Man", crafts_man[0])
        series.append("Lawyer", lawyer[0])
        series.append("Self Employed", selfEmployed[0])

        series.setLabelsVisible(True)

        series.setLabelsPosition(QPieSlice.LabelOutside)
        for slices in series.slices():
            slices.setLabel("{:.2f}%".format(100 * slices.percentage()))

        chart = QChart()
        chart.addSeries(series)
        chart.createDefaultAxes()
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignRight)

        # Set markers for the legend
        chart.legend().markers(series)[0].setLabel("Engineer")
        chart.legend().markers(series)[1].setLabel("Medics")
        chart.legend().markers(series)[2].setLabel("Carpenter")
        chart.legend().markers(series)[3].setLabel("Crafts man")
        chart.legend().markers(series)[4].setLabel("Lawyer")
        chart.legend().markers(series)[5].setLabel("Self Employed")

        # Instantiate chartview class
        chartview = QChartView(chart)
        chartview.setRenderHint(QPainter.Antialiasing)

        # Clear margins of the widget and assign chart to widget
        self.explodedPie.setContentsMargins(0, 0, 0, 0)
        lay1 = QtWidgets.QHBoxLayout(self.explodedPie)
        lay1.setContentsMargins(0, 0, 0, 0)
        lay1.addWidget(chartview)

    def plotClientData(self):
        todayDate = datetime.date.today()
        lastSevenDays = list(map(lambda x: str(todayDate - datetime.timedelta(days=x)), range(0, 7)))
        noOfBurrowedBooks = [self.countValues("Burrow", _) for _ in lastSevenDays]
        noOfBooksSold = [self.countValues("Buy", _) for _ in lastSevenDays]
        rangeVal = noOfBooksSold + noOfBurrowedBooks

        # Create the barset
        set0 = QBarSet('Burrowed')
        set1 = QBarSet('Sold')
        set0.append(noOfBurrowedBooks)
        set1.append(noOfBooksSold)

        series = QBarSeries()
        series.append(set0)
        series.append(set1)

        chart = QChart()
        chart.addSeries(series)
        # chart.setTitle("Books Burrowed in 7 days")
        chart.setAnimationOptions(QChart.SeriesAnimations)

        # lastSevenDays = ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun')
        days = ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')

        axisX = QBarCategoryAxis()
        axisX.append([(str(_[8:]) + 'th') for _ in lastSevenDays])
        axisY = QValueAxis()
        axisY.setRange(0, max(rangeVal))

        chart.addAxis(axisX, Qt.AlignBottom)
        chart.addAxis(axisY, Qt.AlignLeft)

        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignTop)

        chartView = QChartView(chart)
        chartView.setRenderHint(QPainter.Antialiasing)

        self.clientPlot.setContentsMargins(0, 0, 0, 0)

        lay1 = QtWidgets.QVBoxLayout(self.clientPlot)
        lay1.setContentsMargins(0, 0, 0, 0)
        lay1.addWidget(chartView)


class loginWindow(QDialog, loginApp):
    initial = ''

    def __init__(self, parent=None):
        QDialog.__init__(self)
        self.setupUi(self)

        self.status = True
        # Connect to the database
        self.db = MySQLdb.connect(host='localhost', user='root', password='Thebossm@#995', db="library", port=3310)
        self.cur = self.db.cursor()  # Create a cursor

        # Call button handler function
        self.buttonHandler()

        ## ==> REMOVE STANDARD TITLE BAR
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)  # Remove title bar
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)  # Set background to transparent

    def loginHandler(self):
        username = self.usernameLEdit.text()
        password = self.passwordLEdit.text()
        sql = '''SELECT * FROM users '''
        self.cur.execute(sql)
        data = self.cur.fetchall()
        for row in data:
            if username == row[3] and password == row[5]:
                self.error_label.setText('')
                initial = (row[3][0].upper() + row[3][1].upper())
                print(initial)
                self.window2 = MainWindow()
                self.close()
                self.window2.show()
                self.window2.user_initialsLabel.setText(initial)
                MainWindow.currentUser = username
            else:
                self.error_label.setText('Invalid credentials, please try again')

    def buttonHandler(self):
        self.pushButton_4.clicked.connect(self.loginHandler)
        self.logOffBtn.clicked.connect(self.closeWindow)
        self.signUpBtn.clicked.connect(self.openRegisterWindow)
        self.viewPasswordBtn.clicked.connect(self.showPassword)

    def closeWindow(self):
        self.close()

    def openRegisterWindow(self):
        self.regWindow = registerWindow()
        self.close()
        self.regWindow.show()

    def showPassword(self):
        self.status = not self.status
        if not self.status:
            self.passwordLEdit.setEchoMode(QLineEdit.Normal)
        elif self.status:
            self.passwordLEdit.setEchoMode(QLineEdit.Password)


class registerWindow(QDialog, registerApp):
    def __init__(self, parent=None):
        QDialog.__init__(self)
        self.window1 = loginWindow()
        # self = Ui_Dialog_register()
        self.setupUi(self)

        self.passwordStatus = True
        # Connect to the database
        self.db = MySQLdb.connect(host='localhost', user='root', password='Thebossm@#995', db="library", port=3310)
        self.cur = self.db.cursor()  # Create a cursor
        # Call button handler function
        self.buttonHandler1()

        # Remove default title bar
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)  # Remove title bar
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)  # Set background to transparent

    def passwordValidation(self):
        self.error_labelPW.setText('')
        specialCharacters = ["@", '#', '$', '%', '^', '&', '(', ')', '-', "=", "+", '<', '>']
        password = self.passwordLEdit_2.text()
        rep_password = self.repeatpasswordLEdit_3.text()
        errorFlag = False
        check = []

        print(password, rep_password)
        if password != rep_password:
            errorFlag = True
            self.error_labelPW.setText('Passwords do not match')
            print("mismatch")

        if len(password) < 5:
            errorFlag = True
            self.error_labelPW.setText('Password too short')
            print("too short")
        # confirm that there is a special character in the password
        for character in specialCharacters:
            if character not in password:
                check.append('N')
                # print('special character not found')
            else:
                check.append('Y')
        if 'Y' not in check:
            errorFlag = True
            self.error_labelPW.setText('Password must contain special characters')

        if (password == '') and (rep_password == ''):
            errorFlag = True
            self.error_labelPW.setText('Password fields cannot be empty')
            print('empty field')

        return errorFlag

    def usernameValidation(self):
        self.error_labelUN.setText('')
        username = self.usernameLEdit.text()
        errorFlagUN = False
        sql = ''' SELECT * from users'''
        self.cur.execute(sql)
        data = self.cur.fetchall()
        for row in data:
            if username == row[1]:
                self.error_labelUN.setText('Username already exists')
                errorFlagUN = True
        if username == '':
            self.error_labelUN.setText('Username field cannot be empty')
            errorFlagUN = True
        elif len(username) < 4:
            errorFlagUN = True
            self.error_labelUN.setText('Username too short')
        return errorFlagUN

    def emailValidation(self):
        errorFlagEM = False
        email = self.emailLEdit.text()
        self.error_labelEM.setText('')

        if '@' not in email:
            self.error_labelEM.setText('Invalid Email address')
            errorFlagEM = True
        return errorFlagEM

    def addUser(self):
        password = self.passwordLEdit_2.text()
        username = self.usernameLEdit.text()
        email = self.emailLEdit.text()
        er1 = self.emailValidation()
        er2 = self.usernameValidation()
        er3 = self.passwordValidation()

        if (not er1) and (not er2) and (not er3):
            self.cur.execute('''
                    INSERT INTO users(user_name, user_email, user_password) VALUES(%s, %s, %s)
                    ''', (username, email, password))
            self.db.commit()
            self.successLabel.setText('User added successfully. Go back to login page')
        else:
            self.successLabel.setText('Operation unsuccessful')

    def buttonHandler1(self):
        self.pushButton_4.clicked.connect(self.addUser)
        self.signUpBtn.clicked.connect(self.loginWindowOpen)
        self.logOffBtn.clicked.connect(self.closeWindow)
        self.viewPasswordBtn.clicked.connect(self.showPassword)

    def closeWindow(self):
        self.close()

    def loginWindowOpen(self):
        self.close()
        self.window1.show()

    def showPassword(self):
        self.passwordStatus = not self.passwordStatus
        if not self.passwordStatus:
            self.passwordLEdit_2.setEchoMode(QLineEdit.Normal)
            self.repeatpasswordLEdit_3.setEchoMode(QLineEdit.Normal)
        elif self.passwordStatus:
            self.passwordLEdit_2.setEchoMode(QLineEdit.Password)
            self.repeatpasswordLEdit_3.setEchoMode(QLineEdit.Password)


class addNewOperation(QDialog, newOpsApp):

    def __init__(self, parent=None):
        mainW = MainWindow()
        QDialog.__init__(self)
        # self = Ui_Dialog_newOperation()
        # self.ui2 = Ui_MainWindow()
        self.setupUi(self)
        self.setWindowTitle("Add New Operation")

        # Connect to the database
        self.db = MySQLdb.connect(host='localhost', user='root', password='Thebossm@#995', db="library", port=3310)
        self.cur = self.db.cursor()  # Create a cursor

        # Initialize transaction Id generator function
        self.createTransactionId()
        self.var = ''

        # handle buttons on the window
        self.addButton.clicked.connect(self.addNewOperationToDB)
        self.closeBtn.clicked.connect(self.closeWindow)

    def addNewOperationToDB(self):
        noOfDays = self.spinBox.value()
        # Retrieve information in the line edits
        client = self.lineEdit.text()
        activity = self.comboBox.currentText()
        bookID = self.lineEdit_3.text()
        location = self.lineEdit_5.text()
        remarks = self.textEdit.toPlainText()
        username = MainWindow.currentUser
        dateOfOps = datetime.date.today()
        now = time.localtime()
        operation_time = time.strftime("%H:%M", now)
        transactionID = addNewOperation.var
        to = dateOfOps + datetime.timedelta(days=int(noOfDays))
        # make sure number of days is set
        self.cur.execute("SELECT * FROM operations WHERE transaction_id = %s", transactionID)
        check = self.cur.fetchone()

        if check is None:
            if client and activity and bookID and location and remarks:
                self.cur.execute('''
                                    INSERT INTO operations (transaction_id, client, username, book_id, activity, opsdate, time, return_date, location, remarks)
                                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                ''',
                                 (
                                     transactionID, client, username, bookID, activity, dateOfOps, operation_time, to,
                                     location,
                                     remarks))
                self.db.commit()
                showDialog('information', 'Successful Operation', 'Operation has been added to database successfully')

            else:
                showDialog('error', 'Error', 'Field cannot be empty')
        else:
            showDialog('error', 'Error', 'Cannot have duplicate entries. Please close window and retry')

    def createTransactionId(self):
        # generate Transaction ID
        int1 = random.randint(0, 9)
        int2 = random.randint(0, 9)
        letters = string.ascii_uppercase
        result_str = ''.join(random.choice(letters) for i in range(7))

        transactionID = '#' + str(int1) + str(int2) + result_str
        self.transactionID.setText(transactionID)
        addNewOperation.var = transactionID

    def closeWindow(self):
        self.close()

        # MainWindow.show_all_operations(self)


class modifyOperation(QMainWindow, modifyOpsApp):
    def __init__(self):
        QMainWindow.__init__(self)
        # self = Ui_MainWindow_modifyOperation()
        self.setupUi(self)
        self.mainUI = MainWindow()

        # initialize class variables to be used for search
        self.dateOfOps = ''
        self.query = ''
        # Connect to the database
        self.db = MySQLdb.connect(host='localhost', user='root', password='Thebossm@#995', db="library", port=3310)
        self.cur = self.db.cursor()  # Create a cursor

        self.groupBox.setEnabled(False)
        self.searchBtn.clicked.connect(self.searchTrID)
        self.addButton.clicked.connect(self.modifyOpsRecord)
        self.addButton_2.clicked.connect(self.close)

    def searchTrID(self):
        self.query = self.transactionIDSearch.text()

        sql = """SELECT * FROM operations"""
        self.cur.execute(sql)
        data = self.cur.fetchall()
        if data:
            for row in data:
                if self.query == row[0]:
                    self.groupBox.setEnabled(True)
                    self.clientNameEdit.setText(row[1])
                    self.bookIDEdit.setText(row[3])
                    self.typeCombo.setCurrentText(row[4])
                    self.lineEdit_10.setText(row[8])
                    self.textEdit.setPlainText(row[9])
                    self.dateOfOps = row[7]
                    self.statusbar.showMessage("Record found", 3000)
                    break
                else:
                    self.groupBox.setEnabled(False)
                    self.statusbar.showMessage("Record not found, please retry", 3000)

    def modifyOpsRecord(self):
        clName = self.clientNameEdit.text()
        bookID = self.bookIDEdit.text()
        numDays = self.spinBox.value()
        opsType = self.typeCombo.currentText()
        address = self.lineEdit_10.text()
        remark = self.textEdit.toPlainText()
        # noinspection PyTypeChecker
        to = self.dateOfOps + datetime.timedelta(days=int(numDays))

        sql = """UPDATE operations SET
                client = %s,
                book_id = %s,
                activity = %s,
                return_date = %s,
                location = %s,
                remarks = %s
                WHERE transaction_id = %s
              """
        self.cur.execute(sql, (clName, bookID, opsType, to, address, remark, self.query))
        self.db.commit()
        self.showDialog('information', 'Success', 'Record updated successfully')


class progressBar(QMainWindow, progress):
    def __init__(self):
        QMainWindow.__init__(self)
        self.setupUi(self)
        ## ==> SET INITIAL PROGRESS BAR TO (0) ZERO
        self.progressBarValue(0)

        ## ==> REMOVE STANDARD TITLE BAR
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)  # Remove title bar
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)  # Set background to transparent

        ## ==> APPLY DROP SHADOW EFFECT
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(20)
        self.shadow.setXOffset(0)
        self.shadow.setYOffset(0)
        self.shadow.setColor(QColor(0, 0, 0, 120))
        self.circularBg.setGraphicsEffect(self.shadow)

        ## QTIMER ==> START
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.progress)
        # TIMER IN MILLISECONDS
        self.timer.start(10)

        ## SHOW ==> MAIN WINDOW
        ########################################################################
        self.show()
        ## ==> END ##

    ## DEF TO LOANDING
    ########################################################################
    def progress(self):
        global counter
        global jumper
        value = counter

        # HTML TEXT PERCENTAGE
        htmlText = """<p><span style=" font-size:68pt;">{VALUE}</span><span style=" font-size:58pt; 
                        vertical-align:super;">%</span></p>"""

        # REPLACE VALUE
        newHtml = htmlText.replace("{VALUE}", str(jumper))

        if value > jumper:
            # APPLY NEW PERCENTAGE TEXT
            self.labelPercentage.setText(newHtml)
            jumper += 1

        # SET VALUE TO PROGRESS BAR
        # fix max value error if > than 100
        if value >= 100: value = 1.000
        self.progressBarValue(value)

        # CLOSE SPLASH SCREE AND OPEN APP
        if counter > 100:
            # STOP TIMER
            self.timer.stop()

            # SHOW MAIN WINDOW
            self.main = loginWindow()
            self.main.show()

            # CLOSE SPLASH SCREEN
            self.close()

        # INCREASE COUNTER
        counter += 0.5

    ## DEF PROGRESS BAR VALUE
    ########################################################################
    def progressBarValue(self, value):

        # PROGRESSBAR STYLESHEET BASE
        styleSheet = """
            QFrame{
            	border-radius: 150px;
            	background-color: qconicalgradient(cx:0.5, cy:0.5, angle:90, stop:{STOP_1} rgba(255, 0, 127, 0), stop:{STOP_2} rgba(158, 52, 158, 250));
            }
            """

        # GET PROGRESS BAR VALUE, CONVERT TO FLOAT AND INVERT VALUES
        # stop works of 1.000 to 0.000
        progress = (100 - value) / 100.0

        # GET NEW VALUES
        stop_1 = str(progress - 0.001)
        stop_2 = str(progress)

        # SET VALUES TO NEW STYLESHEET
        newStylesheet = styleSheet.replace("{STOP_1}", stop_1).replace("{STOP_2}", stop_2)

        # APPLY STYLESHEET WITH NEW VALUES
        self.circularProgress.setStyleSheet(newStylesheet)


def main():
    app = QtWidgets.QApplication(sys.argv)
    prog = progressBar()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
