"""
------------------------
Model module
The Fabric's SQL Alchemy model classes. These model classes represent tables in DB that are used by the project.
------------------------
Coded by: Krishna Prasad K
© Jyothy Fabricare Services LTD.
------------------------
"""

from fabric import db
from sqlalchemy import CHAR, DECIMAL, ForeignKey, Integer, text, Time, Date, Unicode, Float
from sqlalchemy.dialects.mssql import BIT, UNIQUEIDENTIFIER, TINYINT
from sqlalchemy.orm import relationship


# Edited by MMM
class PaytmEDCTransaction(db.Model):
    """
    This master table contains ranking city which are used to calculate rank of delivery user
    """
    __tablename__ = 'PaytmEDCTransactions'

    Id = db.Column(Integer, primary_key=True)
    OrderId = db.Column(ForeignKey('Orders.OrderId'), nullable=False)
    PaymentStatus = db.Column(db.String(25, 'SQL_Latin1_General_CP1_CI_AS'))
    MerchantTransactionId = db.Column(db.String(200, 'SQL_Latin1_General_CP1_CI_AS'))
    IsDeleted = db.Column(BIT, nullable=False, server_default=text("((0))"))
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    TRNNo = db.Column(db.String(200, 'SQL_Latin1_General_CP1_CI_AS'))

    Order = relationship('Order')


class DeliveryUserEDCDetail(db.Model):
    """
    This master table contains ranking city which are used to calculate rank of delivery user
    """
    __tablename__ = 'DeliveryUserEDCDetails'

    Id = db.Column(Integer, primary_key=True)
    DUserId = db.Column(ForeignKey('DeliveryUsers.DUserId'), nullable=False)
    Tid = db.Column(db.String(50, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    MerchantId = db.Column(db.String(50, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    IsDeleted = db.Column(BIT, nullable=False, server_default=text("((0))"))
    DeviceSerialNumber = db.Column(db.String(50, 'SQL_Latin1_General_CP1_CI_AS'))
    MerchantKey = db.Column(db.String(50, 'SQL_Latin1_General_CP1_CI_AS'))

    DeliveryUser = relationship('DeliveryUser')


class Rankingcityinfo(db.Model):
    """
    This master table contains ranking city which are used to calculate rank of delivery user
    """
    __tablename__ = 'Rankingcityinfo'

    CityCode = db.Column(ForeignKey('Cities.CityCode'), nullable=False)
    CityName = db.Column(db.String(50, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    StateCode = db.Column(db.String(50, 'SQL_Latin1_General_CP1_CI_AS'), primary_key=True)
    StateName = db.Column(db.String(200, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    RankingCity = db.Column(db.String(200, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    RankingCityName = db.Column(db.String(50, 'SQL_Latin1_General_CP1_CI_AS'))

    City = relationship('City')


class DailyCompletedActivityCount(db.Model):
    """
    This master table contains activity count's of delivery user
    """
    __tablename__ = 'DailyCompletedActivityCounts'

    Id = db.Column(Integer, primary_key=True)
    DUserId = db.Column(ForeignKey('DeliveryUsers.DUserId'), nullable=False)
    CityCode = db.Column(ForeignKey('Cities.CityCode'), nullable=False)
    CompletedDate = db.Column(Date, nullable=False)
    PickupCount = db.Column(Integer, nullable=False)
    DeliveryCount = db.Column(Integer, nullable=False)
    IsActive = db.Column(BIT, nullable=False, server_default=text("((1))"))
    IsDeleted = db.Column(BIT, nullable=False, server_default=text("((0))"))
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    PickupRevenue = db.Column(DECIMAL(18, 2))
    DeliveryRevenue = db.Column(DECIMAL(18, 2))

    DeliveryUser = relationship('DeliveryUser')
    City = relationship('City')


class DeliveryUserDailyBranch(db.Model):
    """
    This master table contains branches selected by delivery user daily
    """
    __tablename__ = 'DeliveryUserDailyBranches'

    Id = db.Column(Integer, primary_key=True)
    DUserId = db.Column(ForeignKey('DeliveryUsers.DUserId'), nullable=False)
    BranchCode = db.Column(ForeignKey('Branches.BranchCode'), nullable=False)
    IsActive = db.Column(BIT, nullable=False, server_default=text("((1))"))
    IsDeleted = db.Column(BIT, nullable=False, server_default=text("((0))"))
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordLastUpdatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    IsDefault = db.Column(BIT, nullable=True, server_default=text("((0))"))

    DeliveryUser = relationship('DeliveryUser')
    Branch = relationship('Branch')


class PushNotification(db.Model):
    """
    This master table contains the push notification details.
    """
    __tablename__ = 'PushNotifications'

    PushNotificationId = db.Column(Integer, primary_key=True)
    Message = db.Column(db.String(255, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    DUserId = db.Column(ForeignKey('DeliveryUsers.DUserId'), nullable=False)
    IsRead = db.Column(BIT, nullable=False, server_default=text("((1))"))
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordVersion = db.Column(Integer, nullable=False, server_default=text("((0))"))
    ImageUrl = db.Column(db.String(4000, 'SQL_Latin1_General_CP1_CI_AS'))
    Source = db.Column(db.String(200, 'SQL_Latin1_General_CP1_CI_AS'))
    SentBy = db.Column(Integer, nullable=True)
    IsActive = db.Column(BIT, nullable=False, server_default=text("((1))"))
    IsDeleted = db.Column(BIT, nullable=False, server_default=text("((0))"))
    ReadTime = db.Column(db.DateTime)
    Title = db.Column(db.String(200, 'SQL_Latin1_General_CP1_CI_AS'))

    DeliveryUser = relationship('DeliveryUser')


class CustomerTimeSlot(db.Model):
    """
    This master table contains the push notification details.
    """
    __tablename__ = 'CustomerTimeSlots'

    TimeSlotId = db.Column(Integer, primary_key=True)
    TimeSlot = db.Column(db.String(255, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    TimeSlotFrom = db.Column(Time)
    TimeSlotTo = db.Column(Time)
    IsActive = db.Column(BIT, server_default=text("((1))"))
    IsDeleted = db.Column(BIT, server_default=text("((0))"))


# Edited by MMM
class State(db.Model):
    """
    This master table contains the states' details.
    """
    __tablename__ = 'States'

    StateCode = db.Column(db.String(50, 'SQL_Latin1_General_CP1_CI_AS'), primary_key=True)
    StateName = db.Column(db.String(200, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    IsActive = db.Column(BIT, nullable=False, server_default=text("((1))"))
    IsDeleted = db.Column(BIT, nullable=False, server_default=text("((0))"))
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordLastUpdatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordVersion = db.Column(Integer, nullable=False, server_default=text("((0))"))


class City(db.Model):
    """
    This master table contains the cities' details.
    Relationship(s):
    StateCode is a foreign key referencing StateCode in States table.
    """
    __tablename__ = 'Cities'

    CityCode = db.Column(db.String(50, 'SQL_Latin1_General_CP1_CI_AS'), primary_key=True)
    CityName = db.Column(db.String(200, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    StateCode = db.Column(ForeignKey('States.StateCode'), nullable=False)
    IsActive = db.Column(BIT, nullable=False, server_default=text("((1))"))
    IsDeleted = db.Column(BIT, nullable=False, server_default=text("((0))"))
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordLastUpdatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordVersion = db.Column(Integer, nullable=False, server_default=text("((0))"))

    State = relationship('State')


class Area(db.Model):
    """
    This master table contains the areas' details.
    Relationship(s):
    CityCode is a foreign key referencing CityCode in Cities table.
    """
    __tablename__ = 'Areas'

    AreaCode = db.Column(db.String(50, 'SQL_Latin1_General_CP1_CI_AS'), primary_key=True)
    AreaName = db.Column(db.String(200, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    CityCode = db.Column(ForeignKey('Cities.CityCode'), nullable=False)
    Pincode = db.Column(db.String(10, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    IsActive = db.Column(BIT, nullable=False, server_default=text("((1))"))
    IsDeleted = db.Column(BIT, nullable=False, server_default=text("((0))"))
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordLastUpdatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordVersion = db.Column(Integer, nullable=False, server_default=text("((0))"))

    City = relationship('City')


class Branch(db.Model):
    """
    This master table contains the branches' details (AKA stores').
    Relationship(s):
    AreaCode is a foreign key referencing AreaCode in Areas table.
    """
    __tablename__ = 'Branches'

    BranchCode = db.Column(db.String(50, 'SQL_Latin1_General_CP1_CI_AS'), primary_key=True)
    BranchName = db.Column(db.String(200, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    DisplayName = db.Column(db.String(200, 'SQL_Latin1_General_CP1_CI_AS'))
    BranchAddress = db.Column(db.String(2000, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    PhoneNo = db.Column(db.String(100, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    AreaCode = db.Column(ForeignKey('Areas.AreaCode'), nullable=False)
    RouteCode = db.Column(db.String(50, 'SQL_Latin1_General_CP1_CI_AS'))
    Pincode = db.Column(db.String(10, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    BranchServiceTimeWeekDay = db.Column(db.String(50, 'SQL_Latin1_General_CP1_CI_AS'))
    BranchServiceTimeWeekend = db.Column(db.String(50, 'SQL_Latin1_General_CP1_CI_AS'))
    Lat = db.Column(DECIMAL(13, 10), nullable=False)
    Long = db.Column(DECIMAL(13, 10), nullable=False)
    WeeklyOffDays = db.Column(Integer)
    IsActive = db.Column(BIT, nullable=False, server_default=text("((1))"))
    IsDeleted = db.Column(BIT, nullable=False, server_default=text("((0))"))
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordLastUpdatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordVersion = db.Column(Integer, nullable=False)

    Area = relationship('Area')


class BranchHoliday(db.Model):
    """
    This table contains the holidays of branches.
    """
    __tablename__ = 'BranchHolidays'

    BranchHolidayId = db.Column(Integer, primary_key=True)
    BranchCode = db.Column(db.String(50, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    HolidayDate = db.Column(Date, nullable=False)
    IsActive = db.Column(BIT, nullable=False, server_default=text("((1))"))
    IsDeleted = db.Column(BIT, nullable=False, server_default=text("((0))"))
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordLastUpdatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordVersion = db.Column(Integer, nullable=False, server_default=text("((0))"))


class BranchSeviceTat(db.Model):
    """
    This master table contains all the service tats belongs to a corresponding branches.
    Relationship(s):
    BranchCode is a foreign key referencing BranchCode in Branches table.
    """
    __tablename__ = 'BranchSeviceTats'

    Id = db.Column(Integer, primary_key=True)
    BranchCode = db.Column(ForeignKey('Branches.BranchCode'), nullable=False)
    ServiceTatId = db.Column(Integer, nullable=False)
    IsActive = db.Column(BIT, nullable=False, server_default=text("((1))"))
    IsDeleted = db.Column(BIT, nullable=False, server_default=text("((0))"))
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordLastUpdatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordVersion = db.Column(Integer, nullable=False, server_default=text("((0))"))

    Branch = relationship('Branch')


class GarmentCategory(db.Model):
    """
    This master table contains category information of all the garments.
    """
    __tablename__ = 'GarmentCategories'

    CategoryId = db.Column(Integer, primary_key=True)
    CategoryName = db.Column(db.String(50, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    Description = db.Column(db.String(200, 'SQL_Latin1_General_CP1_CI_AS'))
    IsActive = db.Column(BIT, nullable=False, server_default=text("((1))"))
    IsDeleted = db.Column(BIT, nullable=False, server_default=text("((0))"))
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordLastUpdatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordVersion = db.Column(Integer, nullable=False, server_default=text("((0))"))


class GarmentUOM(db.Model):
    """
    This master table contains the unit of measurement (UOM) details.
    """
    __tablename__ = 'GarmentUOMs'

    UOMId = db.Column(Integer, primary_key=True)
    UOMName = db.Column(db.String(50, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    Description = db.Column(db.String(200, 'SQL_Latin1_General_CP1_CI_AS'))
    IsActive = db.Column(BIT, nullable=False, server_default=text("((1))"))
    IsDeleted = db.Column(BIT, nullable=False, server_default=text("((0))"))
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordLastUpdatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordVersion = db.Column(Integer, nullable=False, server_default=text("((0))"))


class GarmentInstruction(db.Model):
    """
    This master table contains the instructions that can be applied on a garment upon order creation.
    """
    __tablename__ = 'GarmentInstructions'

    InstructionId = db.Column(Integer, primary_key=True)
    InstructionName = db.Column(db.String(50, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    InstructionDescription = db.Column(db.String(100, 'SQL_Latin1_General_CP1_CI_AS'))
    InstructionIcon = db.Column(db.String(50, 'SQL_Latin1_General_CP1_CI_AS'))
    IsActive = db.Column(BIT, nullable=False, server_default=text("((1))"))
    IsDeleted = db.Column(BIT, nullable=False, server_default=text("((0))"))
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordLastUpdatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordVersion = db.Column(Integer, nullable=False, server_default=text("((0))"))


class GarmentIssue(db.Model):
    """
    This master table contains the issues that can be applied on a garment upon order creation.
    """
    __tablename__ = 'GarmentIssues'

    IssueId = db.Column(Integer, primary_key=True)
    IssueName = db.Column(db.String(50, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    IssueDescription = db.Column(db.String(100, 'SQL_Latin1_General_CP1_CI_AS'))
    IssueIcon = db.Column(db.String(50, 'SQL_Latin1_General_CP1_CI_AS'))
    IsActive = db.Column(BIT, nullable=False, server_default=text("((1))"))
    IsDeleted = db.Column(BIT, nullable=False, server_default=text("((0))"))
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordLastUpdatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordVersion = db.Column(Integer, nullable=False, server_default=text("((0))"))


class GarmentStatusCode(db.Model):
    """
    This master table contains the status codes for a garment.
    """
    __tablename__ = 'GarmentStatusCodes'

    GarmentStatusId = db.Column(Integer, primary_key=True)
    StatusCode = db.Column(Unicode(200), nullable=False)
    PosStatusCode = db.Column(Unicode(200), nullable=False)
    IsDeleted = db.Column(BIT, nullable=False, server_default=text("((0))"))
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordLastUpdatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordVersion = db.Column(Integer, nullable=False, server_default=text("((0))"))


class Garment(db.Model):
    """
    This master table contains the all the garment details.
    Relationship(s):
    CategoryId is a foreign key referencing CategoryId in GarmentCategories table.
    UOMId is a foreign key referencing UOMId in GarmentUOMs table.
    """
    __tablename__ = 'Garments'

    GarmentId = db.Column(Integer, primary_key=True)
    GarmentName = db.Column(db.String(200, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    Description = db.Column(db.String(200, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    CategoryId = db.Column(ForeignKey('GarmentCategories.CategoryId'), nullable=False)
    UOMId = db.Column(ForeignKey('GarmentUOMs.UOMId'), nullable=False)
    GarmentIcon = db.Column(db.String(200, 'SQL_Latin1_General_CP1_CI_AS'))
    GarmentPreference = db.Column(Integer)
    IsActive = db.Column(BIT, nullable=False, server_default=text("((1))"))
    IsDeleted = db.Column(BIT, nullable=False, server_default=text("((0))"))
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordLastUpdatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordVersion = db.Column(Integer, nullable=False, server_default=text("((0))"))

    GarmentCategory = relationship('GarmentCategory')
    GarmentUOM = relationship('GarmentUOM')


class ServiceTat(db.Model):
    """
    This master table contains the service turn around time (TAT) details.
    """
    __tablename__ = 'ServiceTats'

    ServiceTatId = db.Column(Integer, primary_key=True)
    ServiceTatName = db.Column(db.String(200, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    ServiceTatIcon = db.Column(db.String(50, 'SQL_Latin1_General_CP1_CI_AS'))
    IsActive = db.Column(BIT, nullable=False, server_default=text("((1))"))
    IsDeleted = db.Column(BIT, nullable=False, server_default=text("((0))"))
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordLastUpdatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordVersion = db.Column(Integer, nullable=False, server_default=text("((0))"))


class ServiceType(db.Model):
    """
    This master table contains the service types details.
    """
    __tablename__ = 'ServiceTypes'

    ServiceTypeId = db.Column(Integer, primary_key=True)
    ServiceTypeName = db.Column(db.String(200, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    ServiceDescription = db.Column(db.String(100, 'SQL_Latin1_General_CP1_CI_AS'))
    ServiceTypeIcon = db.Column(db.String(50, 'SQL_Latin1_General_CP1_CI_AS'))
    IsVAS = db.Column(BIT, nullable=False)
    IsActive = db.Column(BIT, nullable=False, server_default=text("((1))"))
    IsDeleted = db.Column(BIT, nullable=False, server_default=text("((0))"))
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordLastUpdatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordVersion = db.Column(Integer, nullable=False, server_default=text("((0))"))


class PriceList(db.Model):
    """
    This master table contains the price list of a particular garment. Price may vary based on combination of
    branch code, service tat, and service type.
    Relationship(s):
    BranchCode is a foreign key referencing BranchCode in Branches table.
    ServiceTatId is a foreign key referencing ServiceTatId in ServiceTats table.
    ServiceTypeId is a foreign key referencing ServiceTypeId in ServiceTypes table.
    GarmentId is a foreign key referencing GarmentId in Garments table.
    """
    __tablename__ = 'PriceList'

    Id = db.Column(Integer, primary_key=True)
    # Edited by MMM
    IsHanger = db.Column(BIT, nullable=False, server_default=text("((0))"))
    # Edited by MMM
    GarmentId = db.Column(ForeignKey('Garments.GarmentId'), nullable=False)
    BranchCode = db.Column(ForeignKey('Branches.BranchCode'), nullable=False)
    ServiceTatId = db.Column(ForeignKey('ServiceTats.ServiceTatId'), nullable=False)
    ServiceTypeId = db.Column(ForeignKey('ServiceTypes.ServiceTypeId'), nullable=False)
    Price = db.Column(DECIMAL(18, 2), nullable=False)
    IsActive = db.Column(BIT, nullable=False, server_default=text("((1))"))
    IsDeleted = db.Column(BIT, nullable=False, server_default=text("((0))"))
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordLastUpdatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordVersion = db.Column(Integer, nullable=False, server_default=text("((0))"))

    Branch = relationship('Branch')
    Garment = relationship('Garment')
    ServiceTat = relationship('ServiceTat')
    ServiceType = relationship('ServiceType')


class Customer(db.Model):
    """
    This master table contains the customer details.
    Relationship(s):
    BranchCode is a foreign key referencing BranchCode in Branches table.
    CityCode is a foreign key referencing CityCode in Cities table.
    """
    __tablename__ = 'Customers'

    CustomerId = db.Column(Integer, primary_key=True)
    CustomerCode = db.Column(db.String(20, 'SQL_Latin1_General_CP1_CI_AS'))
    CustomerName = db.Column(db.String(500, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    MobileNo = db.Column(db.String(20, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    AlternateNo = db.Column(db.String(20, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    Password = db.Column(db.String(500, 'SQL_Latin1_General_CP1_CI_AS'))
    EmailId = db.Column(db.String(500, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    SocialLoginType = db.Column(CHAR(1, 'SQL_Latin1_General_CP1_CI_AS'))
    SocialLoginId = db.Column(db.String(200, 'SQL_Latin1_General_CP1_CI_AS'))
    CityCode = db.Column(ForeignKey('Cities.CityCode'), nullable=False)
    IsWhatsAppSubscribed = db.Column(BIT, nullable=False, server_default=text("((0))"))
    Photo = db.Column(db.String(500, 'SQL_Latin1_General_CP1_CI_AS'))
    IsProfileComplete = db.Column(BIT, nullable=False, server_default=text("((0))"))
    IsEmailVerified = db.Column(BIT, nullable=False, server_default=text("((0))"))
    EmailVerifiedDate = db.Column(db.DateTime)
    Gender = db.Column(CHAR(1, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False, server_default=text("('N')"))
    DateOfBirth = db.Column(Date)
    Occupation = db.Column(db.String(500, 'SQL_Latin1_General_CP1_CI_AS'))
    RegisteredDate = db.Column(db.DateTime, nullable=False)
    BranchCode = db.Column(ForeignKey('Branches.BranchCode'), nullable=False)
    CreatedFrom = db.Column(db.String(50, 'SQL_Latin1_General_CP1_CI_AS'))
    IsERRegister = db.Column(BIT)
    IsWhatsApp = db.Column(BIT)
    IsOptIn = db.Column(BIT)
    IsActive = db.Column(BIT, nullable=False, server_default=text("((1))"))
    IsDeleted = db.Column(BIT, nullable=False, server_default=text("((0))"))
    IsNew = db.Column(BIT)
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordLastUpdatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordVersion = db.Column(Integer, nullable=False, server_default=text("((0))"))
    MonthlyCustomer = db.Column(BIT, nullable=False, server_default=text("((0))"))
    Source = db.Column(db.String(500, 'SQL_Latin1_General_CP1_CI_AS'))

    Branch = relationship('Branch')
    City = relationship('City')


class CustomerAddres(db.Model):
    """
    This table contains the address details customers.
    Relationship(s):
    CustomerId is a foreign key referencing CustomerId in Customers table.
    AreaCode is a foreign key referencing AreaCode in Areas table.
    CityCode is a foreign key referencing CityCode in Cities table.
    """
    __tablename__ = 'CustomerAddress'

    CustAddressId = db.Column(Integer, primary_key=True)
    CustomerId = db.Column(ForeignKey('Customers.CustomerId'), nullable=False)
    AddressName = db.Column(db.String(20, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    AddressLine1 = db.Column(db.String(500, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    AddressLine2 = db.Column(db.String(500, 'SQL_Latin1_General_CP1_CI_AS'))
    AddressLine3 = db.Column(db.String(500, 'SQL_Latin1_General_CP1_CI_AS'))
    Landmark = db.Column(db.String(500, 'SQL_Latin1_General_CP1_CI_AS'))
    Pincode = db.Column(db.String(10, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    AreaCode = db.Column(ForeignKey('Areas.AreaCode'), nullable=False)
    CityCode = db.Column(ForeignKey('Cities.CityCode'), nullable=False)
    Lat = db.Column(DECIMAL(13, 10))
    Long = db.Column(DECIMAL(13, 10))
    IsActive = db.Column(BIT, nullable=False, server_default=text("((1))"))
    IsDeleted = db.Column(BIT, nullable=False, server_default=text("((0))"))
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordLastUpdatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordVersion = db.Column(Integer, nullable=False, server_default=text("((0))"))
    GeoLocation = db.Column(db.String(500, 'SQL_Latin1_General_CP1_CI_AS'))

    Area = relationship('Area')
    City = relationship('City')
    Customer = relationship('Customer')


class PickupRequest(db.Model):
    """
    This table contains the pickup requests created by customer/delivery person. The data can be inserted from either
    customer app/delivery app or from the Fabricare itself.
    Relationship(s):
    CustomerId is a foreign key referencing CustomerId in Customers table.
    PickupTimeSlotId is a foreign key referencing PickupTimeSlotId in PickupTimeSlots table.
    BranchCode is a foreign key referencing BranchCode in Branches table.
    CustAddressId is a foreign key referencing CustAddressId in CustomerAddress table.
    PickupStatusId is a foreign key referencing PickupStatusId in PickupStatusCodes table.
    DUserId is a foreign key referencing DUserId in DeliveryUsers table.
    CancelReasonId is a foreign key referencing CancelReasonId in PickupCancelReasons table.
    CancelledDeliveryUser is a foreign key referencing DUserId in DeliveryUsers table.
    CancelledStoreUser is a foreign key referencing SUserId in StoreUsers table.
    AssignedStoreUser is a foreign key referencing SUserId in StoreUsers table.
    ServiceTatId is a foreign key referencing ServiceTatId in ServiceTats table.
    """
    __tablename__ = 'PickupRequests'

    PickupRequestId = db.Column(Integer, primary_key=True)
    CustomerId = db.Column(ForeignKey('Customers.CustomerId'), nullable=False)
    PickupDate = db.Column(db.DateTime, nullable=False)
    PickupTimeSlotId = db.Column(ForeignKey('FabPickupTimeSlots.PickupTimeSlotId'))
    TimeSlotFrom = db.Column(Time)
    TimeSlotTo = db.Column(Time)
    BranchCode = db.Column(ForeignKey('Branches.BranchCode'), nullable=False)
    CustAddressId = db.Column(ForeignKey('CustomerAddress.CustAddressId'), nullable=False)
    PickupSource = db.Column(db.String(50, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    DiscountCode = db.Column(db.String(50, 'SQL_Latin1_General_CP1_CI_AS'))
    CouponCode = db.Column(db.String(50, 'SQL_Latin1_General_CP1_CI_AS'))
    ApplyLoyalityPoints = db.Column(BIT, nullable=False, server_default=text("((0))"))
    BookingId = db.Column(db.String(200, 'SQL_Latin1_General_CP1_CI_AS'))
    PickupStatusId = db.Column(ForeignKey('PickupStatusCodes.PickupStatusId'), nullable=False)
    DUserId = db.Column(ForeignKey('DeliveryUsers.DUserId'))
    CodeFromER = db.Column(db.String(200, 'SQL_Latin1_General_CP1_CI_AS'))
    ERRequestId = db.Column(db.String(100, 'SQL_Latin1_General_CP1_CI_AS'))
    IsERCoupon = db.Column(BIT)
    IsCancelled = db.Column(BIT, nullable=False, server_default=text("((0))"))
    IsRescheduled = db.Column(BIT, nullable=False, server_default=text("((0))"))
    Remarks = db.Column(db.String(500, 'SQL_Latin1_General_CP1_CI_AS'))
    CancelReasonId = db.Column(ForeignKey('PickupCancelReasons.CancelReasonId'))
    CancelledDate = db.Column(db.DateTime)
    CancelRemarks = db.Column(db.String(500, 'SQL_Latin1_General_CP1_CI_AS'))
    CancelledBy = db.Column(db.String(100, 'SQL_Latin1_General_CP1_CI_AS'))
    CancelledRefId = db.Column(Integer)
    CancelledStoreUser = db.Column(ForeignKey('StoreUsers.SUserId'))
    CancelledDeliveryUser = db.Column(ForeignKey('DeliveryUsers.DUserId'))
    AssignedStoreUser = db.Column(ForeignKey('StoreUsers.SUserId'))
    AssignedDate = db.Column(db.DateTime)
    CompletedDate = db.Column(db.DateTime)
    # This Lat & Long is using for saving the pickup cancellation geo-location.
    Lat = db.Column(DECIMAL(13, 10))
    Long = db.Column(DECIMAL(13, 10))
    ServiceTatId = db.Column(ForeignKey('ServiceTats.ServiceTatId'))
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordLastUpdatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordVersion = db.Column(Integer, nullable=False, server_default=text("((0))"))
    # Edited by MMM
    AdhocDiscount = db.Column(db.String(50, 'SQL_Latin1_General_CP1_CI_AS'))
    AdhocCoupon = db.Column(db.String(50, 'SQL_Latin1_General_CP1_CI_AS'))
    CompletedBy = db.Column(Integer)
    GeoLocation = db.Column(db.String(500, 'SQL_Latin1_General_CP1_CI_AS'))
    IsReopen = db.Column(BIT, nullable=False, server_default=text("((0))"))
    WashType = db.Column(db.String(100, 'SQL_Latin1_General_CP1_CI_AS'))
    # Edited by MMM

    StoreUser = relationship('StoreUser', primaryjoin='PickupRequest.AssignedStoreUser == StoreUser.SUserId')
    Branch = relationship('Branch')
    PickupCancelReason = relationship('PickupCancelReason')
    DeliveryUser = relationship('DeliveryUser',
                                primaryjoin='PickupRequest.CancelledDeliveryUser == DeliveryUser.DUserId')
    StoreUser1 = relationship('StoreUser', primaryjoin='PickupRequest.CancelledStoreUser == StoreUser.SUserId')
    CustomerAddres = relationship('CustomerAddres')
    Customer = relationship('Customer')
    DeliveryUser1 = relationship('DeliveryUser', primaryjoin='PickupRequest.DUserId == DeliveryUser.DUserId')
    PickupStatusCode = relationship('PickupStatusCode')
    FabPickupTimeSlots = relationship('FabPickupTimeSlots')
    ServiceTat = relationship('ServiceTat')
    inlocation = db.Column(db.String(25, 'SQL_Latin1_General_CP1_CI_AS'))
    distance = db.Column(db.String(50, 'SQL_Latin1_General_CP1_CI_AS'))
    store_distance = db.Column(db.String(50, 'SQL_Latin1_General_CP1_CI_AS'))
    DuserLat = db.Column(Float(53))
    DuserLong = db.Column(Float(53))

    # Laji
    ReschuduleStatus = db.Column(Integer)
    ReschuduleDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    ReschuduleBy = db.Column(Integer)
    ReschuduleAddressId = db.Column(Integer)
    ReschuduleModifiedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    ReschuduleTimeSlotId = db.Column(Integer)
    ReschuduleTimeSlotFrom = db.Column(db.String(100, 'SQL_Latin1_General_CP1_CI_AS'))
    ReschuduleTimeSlotTo = db.Column(db.String(100, 'SQL_Latin1_General_CP1_CI_AS'))


class PickupCancelReason(db.Model):
    """
    This master table contains the predefined reasons for pickup requests cancellation.
    """
    __tablename__ = 'PickupCancelReasons'

    CancelReasonId = db.Column(Integer, primary_key=True)
    CancelReason = db.Column(Unicode(500), nullable=False)
    IsDeleted = db.Column(BIT, nullable=False, server_default=text("((0))"))
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordLastUpdatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordVersion = db.Column(Integer, nullable=False, server_default=text("((0))"))


class PickupRescheduleReason(db.Model):
    """
    This master table contains the predefined reasons for pickup reschedule.
    """
    __tablename__ = 'PickupRescheduleReasons'

    RescheduleReasonId = db.Column(Integer, primary_key=True)
    RescheduleReason = db.Column(Unicode(500), nullable=False)
    IsDeleted = db.Column(BIT, nullable=False, server_default=text("((0))"))
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordLastUpdatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordVersion = db.Column(Integer, nullable=False, server_default=text("((0))"))


class PickupReschedule(db.Model):
    """
    This table contains the reschedules made for corresponding pickup requests.
    Relationship(s):
    PickupRequestId is a foreign key referencing PickupRequestId in PickupRequests table.
    RescheduleReasonId is a foreign key referencing RescheduleReasonId in RescheduleReasons table.
    PickupTimeSlotId is a foreign key referencing PickupTimeSlotId in PickupTimeSlots table.
    BranchCode is a foreign key referencing BranchCode in Branches table.
    DUserId is a foreign key referencing DUserId in DeliveryUsers table.
    CustAddressId is a foreign key referencing CustAddressId in CustomerAddress table.
    RescheduledStoreUser is a foreign key referencing SUserId in StoreUsers table.
    RescheduledDeliveryUser is a foreign key referencing DUserId in DeliveryUsers table.
    AssignedStoreUser is a foreign key referencing SUserId in StoreUsers table.
    """
    __tablename__ = 'PickupReschedules'

    Id = db.Column(Integer, primary_key=True)
    PickupRequestId = db.Column(ForeignKey('PickupRequests.PickupRequestId'), nullable=False)
    RescheduleReasonId = db.Column(ForeignKey('PickupRescheduleReasons.RescheduleReasonId'), nullable=False)
    RescheduledDate = db.Column(Date, nullable=False)
    PickupTimeSlotId = db.Column(ForeignKey('FabPickupTimeSlots.PickupTimeSlotId'))
    TimeSlotFrom = db.Column(Time)
    TimeSlotTo = db.Column(Time)
    RescheduleRemarks = db.Column(db.String(500, 'SQL_Latin1_General_CP1_CI_AS'))
    BranchCode = db.Column(ForeignKey('Branches.BranchCode'), nullable=False)
    DUserId = db.Column(ForeignKey('DeliveryUsers.DUserId'))
    CustAddressId = db.Column(ForeignKey('CustomerAddress.CustAddressId'), nullable=False)
    RescheduledBy = db.Column(db.String(2, 'SQL_Latin1_General_CP1_CI_AS'))
    RefId = db.Column(Integer)
    IsDeleted = db.Column(BIT, nullable=False, server_default=text("((0))"))
    RescheduledStoreUser = db.Column(ForeignKey('StoreUsers.SUserId'), ForeignKey('StoreUsers.SUserId'))
    RescheduledDeliveryUser = db.Column(ForeignKey('DeliveryUsers.DUserId'))
    CancelledDate = db.Column(db.DateTime)
    AssignedStoreUser = db.Column(ForeignKey('StoreUsers.SUserId'))
    AssignedDate = db.Column(db.DateTime)
    # This Lat & Long is using for saving the pickup rescheduling geo-location.
    Lat = db.Column(DECIMAL(13, 10))
    Long = db.Column(DECIMAL(13, 10))
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordLastUpdatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordVersion = db.Column(Integer, nullable=False, server_default=text("((0))"))

    StoreUser = relationship('StoreUser', primaryjoin='PickupReschedule.AssignedStoreUser == StoreUser.SUserId')
    Branch = relationship('Branch')
    CustomerAddres = relationship('CustomerAddres')
    DeliveryUser = relationship('DeliveryUser', primaryjoin='PickupReschedule.DUserId == DeliveryUser.DUserId')
    PickupRequest = relationship('PickupRequest')
    FabPickupTimeSlots = relationship('FabPickupTimeSlots')
    PickupRescheduleReason = relationship('PickupRescheduleReason')
    DeliveryUser1 = relationship('DeliveryUser',
                                 primaryjoin='PickupReschedule.RescheduledDeliveryUser == DeliveryUser.DUserId')
    StoreUser1 = relationship('StoreUser', primaryjoin='PickupReschedule.RescheduledStoreUser == StoreUser.SUserId')
    StoreUser2 = relationship('StoreUser', primaryjoin='PickupReschedule.RescheduledStoreUser == StoreUser.SUserId')


class PickupStatusCode(db.Model):
    """
    This master table contains the status codes for a pickup request.
    """
    __tablename__ = 'PickupStatusCodes'

    PickupStatusId = db.Column(Integer, primary_key=True)
    StatusCode = db.Column(Unicode(200), nullable=False)
    PosStatusCode = db.Column(Unicode(200), nullable=False)
    IsDeleted = db.Column(BIT, nullable=False, server_default=text("((0))"))
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordLastUpdatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordVersion = db.Column(Integer, nullable=False, server_default=text("((0))"))


class PickupTimeSlot(db.Model):
    """
    This master table contains the pickup time slots based on branch codes.
    Relationship(s):
    BranchCode is a foreign key referencing BranchCode in Branches table.
    """
    __tablename__ = 'PickupTimeSlots'

    PickupTimeSlotId = db.Column(Integer, primary_key=True)
    FabricareTimeSlotId = db.Column(Integer, nullable=False)
    BranchCode = db.Column(ForeignKey('Branches.BranchCode'), nullable=False)
    TimeSlotFrom = db.Column(Time, nullable=False)
    TimeSlotTo = db.Column(Time, nullable=False)
    DefaultFlag = db.Column(BIT, nullable=False, server_default=text("((0))"))
    VisibilityFlag = db.Column(BIT, nullable=False, server_default=text("((1))"))
    DayType = db.Column(Integer, nullable=False)
    IsActive = db.Column(BIT, nullable=False, server_default=text("((1))"))
    IsDeleted = db.Column(BIT, nullable=False, server_default=text("((0))"))
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordLastUpdatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordVersion = db.Column(Integer, nullable=False, server_default=text("((0))"))

    Branch = relationship('Branch')


class PickupReqServiceTat(db.Model):
    """
    This table contains the service tats attached to corresponding pickup requests.
    Relationship(s):
    PickupRequestId is a foreign key referencing PickupRequestId in PickupRequests table.
    ServiceTatId is a foreign key referencing ServiceTatId in ServiceTats table.
    """
    __tablename__ = 'PickupReqServiceTats'

    Id = db.Column(Integer, primary_key=True)
    PickupRequestId = db.Column(ForeignKey('PickupRequests.PickupRequestId'), nullable=False)
    ServiceTatId = db.Column(ForeignKey('ServiceTats.ServiceTatId'), nullable=False)
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordLastUpdatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordVersion = db.Column(Integer, nullable=False, server_default=text("((0))"))

    PickupRequest = relationship('PickupRequest')
    ServiceTat = relationship('ServiceTat')


class PickupReqService(db.Model):
    """
    This table contains the service types that are attached to corresponding pickup requests.
    Relationship(s):
    PickupRequestId is a foreign key referencing PickupRequestId in PickupRequests table.
    ServiceTypeId is a foreign key referencing ServiceTypeId in ServiceTypes table.
    """
    __tablename__ = 'PickupReqServices'

    Id = db.Column(Integer, primary_key=True)
    PickupRequestId = db.Column(ForeignKey('PickupRequests.PickupRequestId'), nullable=False)
    ServiceTypeId = db.Column(ForeignKey('ServiceTypes.ServiceTypeId'), nullable=False)
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordLastUpdatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordVersion = db.Column(Integer, nullable=False, server_default=text("((0))"))

    PickupRequest = relationship('PickupRequest')
    ServiceType = relationship('ServiceType')


class Order(db.Model):
    """
    This table contains the order details. Data can be inserted either while collecting garments from customer
    or directly from Fabricare itself.
    Relationship(s):
    CustomerId is a foreign key referencing CustomerId in Customers table.
    BranchCode is a foreign key referencing BranchCode in Branches table.
    PickupRequestId is a foreign key referencing PickupRequestId in PickupRequests table.
    PickupAddressId is a foreign key referencing CustAddressId in CustomerAddress table.
    DeliveryAddressId is a foreign key referencing CustAddressId in CustomerAddress table.
    DUserId is a foreign key referencing DUserId in DeliveryUsers table.
    OrderTypeId is a foreign key referencing OrderTypeId in OrderTypes table.
    """
    __tablename__ = 'Orders'

    OrderId = db.Column(Integer, primary_key=True)
    OrderCode = db.Column(db.String(50, 'SQL_Latin1_General_CP1_CI_AS'))
    EGRN = db.Column(db.String(50, 'SQL_Latin1_General_CP1_CI_AS'))
    CustomerId = db.Column(ForeignKey('Customers.CustomerId'), nullable=False)
    BranchCode = db.Column(ForeignKey('Branches.BranchCode'), nullable=False)
    PickupRequestId = db.Column(ForeignKey('PickupRequests.PickupRequestId'))
    TimeSlotFrom = db.Column(Time)
    TimeSlotTo = db.Column(Time)
    BookingId = db.Column(db.String(200, 'SQL_Latin1_General_CP1_CI_AS'))
    PickupAddressId = db.Column(ForeignKey('CustomerAddress.CustAddressId'))
    DeliveryAddressId = db.Column(ForeignKey('CustomerAddress.CustAddressId'))
    PickupDate = db.Column(db.DateTime)
    DUserId = db.Column(ForeignKey('DeliveryUsers.DUserId'))
    Remarks = db.Column(db.String(500, 'SQL_Latin1_General_CP1_CI_AS'))
    DiscountCode = db.Column(db.String(50, 'SQL_Latin1_General_CP1_CI_AS'))
    CouponCode = db.Column(db.String(50, 'SQL_Latin1_General_CP1_CI_AS'))
    LoyalityPoints = db.Column(Integer)
    OrderTypeId = db.Column(ForeignKey('OrderTypes.OrderTypeId'))
    OrderDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    EstDeliveryDate = db.Column(db.DateTime)
    BasicAmount = db.Column(DECIMAL(18, 2))
    Discount = db.Column(DECIMAL(18, 2), nullable=False, server_default=text("((0.0))"))
    ServiceTaxAmount = db.Column(DECIMAL(18, 2))
    OrderAmount = db.Column(DECIMAL(18, 2))
    OrderStatusId = db.Column(ForeignKey('OrderStatusCodes.OrderStatusId'), nullable=False)
    CodeFromER = db.Column(db.String(200, 'SQL_Latin1_General_CP1_CI_AS'))
    ERRequestId = db.Column(db.String(100, 'SQL_Latin1_General_CP1_CI_AS'))
    IsERCoupon = db.Column(BIT)
    IsDeleted = db.Column(BIT, nullable=False, server_default=text("((0))"))
    ReOpenStatus = db.Column(BIT, nullable=False, server_default=text("((0))"))
    DeliveryCharge = db.Column(BIT)
    DeliveryChargeFlag = db.Column(BIT)
    # This Lat & Long is using for saving the geo-location while creating the order.
    Lat = db.Column(DECIMAL(13, 10))
    Long = db.Column(DECIMAL(13, 10))
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordLastUpdatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordVersion = db.Column(Integer, nullable=False, server_default=text("((0))"))
    InsertedBy = db.Column(db.String(200))

    Branch = relationship('Branch')
    Customer = relationship('Customer')
    DeliveryUser = relationship('DeliveryUser')
    CustomerAddres = relationship('CustomerAddres',
                                  primaryjoin='Order.DeliveryAddressId == CustomerAddres.CustAddressId')
    OrderStatusCode = relationship('OrderStatusCode')
    OrderType = relationship('OrderType')
    CustomerAddres1 = relationship('CustomerAddres',
                                   primaryjoin='Order.PickupAddressId == CustomerAddres.CustAddressId')
    PickupRequest = relationship('PickupRequest')


class OrderType(db.Model):
    """
    This master table contains the order types. Eg. Normal, rewash..etc.
    """
    __tablename__ = 'OrderTypes'

    OrderTypeId = db.Column(Integer, primary_key=True)
    IsDeleted = db.Column(BIT, nullable=False, server_default=text("((0))"))
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordLastUpdatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordVersion = db.Column(Integer, nullable=False, server_default=text("((0))"))


class OrderStatusCode(db.Model):
    __tablename__ = 'OrderStatusCodes'

    OrderStatusId = db.Column(Integer, primary_key=True)
    StatusCode = db.Column(Unicode(200), nullable=False)
    PosStatusCode = db.Column(Unicode(200), nullable=False)
    IsDeleted = db.Column(BIT, nullable=False, server_default=text("((0))"))
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordLastUpdatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordVersion = db.Column(Integer, nullable=False, server_default=text("((0))"))


class OrderGarment(db.Model):
    """
    This table contains the attached garments to corresponding orders.
    Relationship(s):
    OrderId is a foreign key referencing OrderId in Orders table.
    GarmentId is a foreign key referencing GarmentId in Garments table.
    ServiceTypeId is a foreign key referencing ServiceTypeId in ServiceTypes table.
    ServiceTatId is a foreign key referencing ServiceTatId in ServiceTats table.
    GarmentStatusId is a foreign key referencing GarmentStatusId in GarmentStatusCodes table.
    """
    __tablename__ = 'OrderGarments'

    OrderGarmentId = db.Column(Integer, primary_key=True)
    OrderId = db.Column(ForeignKey('Orders.OrderId'), nullable=False)
    POSOrderGarmentId = db.Column(UNIQUEIDENTIFIER)
    GarmentId = db.Column(ForeignKey('Garments.GarmentId'), nullable=False)
    ServiceTypeId = db.Column(ForeignKey('ServiceTypes.ServiceTypeId'), nullable=False)
    ServiceTatId = db.Column(ForeignKey('ServiceTats.ServiceTatId'), nullable=False)
    TagId = db.Column(db.String(50, 'SQL_Latin1_General_CP1_CI_AS'))
    GarmentStatusId = db.Column(ForeignKey('GarmentStatusCodes.GarmentStatusId'), nullable=False)
    GarmentBrand = db.Column(db.String(50, 'SQL_Latin1_General_CP1_CI_AS'))
    GarmentColour = db.Column(db.String(50, 'SQL_Latin1_General_CP1_CI_AS'))
    GarmentSize = db.Column(db.String(50, 'SQL_Latin1_General_CP1_CI_AS'))
    QCStatus = db.Column(Integer)
    CRMComplaintId = db.Column(Integer)
    Length = db.Column(Float(53))
    Width = db.Column(Float(53))
    Sqft = db.Column(Float(53))
    BasicAmount = db.Column(DECIMAL(18, 2), nullable=False)
    Discount = db.Column(DECIMAL(18, 2), nullable=False, server_default=text("((0.0))"))
    ServiceTaxAmount = db.Column(DECIMAL(18, 2))
    EstDeliveryDate = db.Column(db.DateTime)
    IsDeleted = db.Column(BIT, nullable=False, server_default=text("((0))"))
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordLastUpdatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordVersion = db.Column(Integer, nullable=False, server_default=text("((0))"))
    DarningGarmentLength = db.Column(DECIMAL(13, 2))
    InsertedBy = db.Column(db.String(200))

    Garment = relationship('Garment')
    GarmentStatusCode = relationship('GarmentStatusCode')
    Order = relationship('Order')
    ServiceTat = relationship('ServiceTat')
    ServiceType = relationship('ServiceType')


class OrderInstruction(db.Model):
    """
    This table contains the instructions attached to corresponding order garments.
    Relationship(s):
    OrderId is a foreign key referencing OrderId in Orders table.
    OrderGarmentId is a foreign key referencing OrderGarmentId in OrderGarments table.
    InstructionId is a foreign key referencing InstructionId in GarmentInstructions table.
    """
    __tablename__ = 'OrderInstructions'

    OrderInstructionId = db.Column(Integer, primary_key=True)
    OrderId = db.Column(ForeignKey('Orders.OrderId'), nullable=False)
    OrderGarmentId = db.Column(ForeignKey('OrderGarments.OrderGarmentId'), nullable=False)
    InstructionId = db.Column(ForeignKey('GarmentInstructions.InstructionId'), nullable=False)
    IsDeleted = db.Column(BIT, nullable=False, server_default=text("((0))"))
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordLastUpdatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordVersion = db.Column(Integer, nullable=False, server_default=text("((0))"))
    DarningGarmentLength = db.Column(DECIMAL(13, 2))
    DarningGarmentAmount = db.Column(DECIMAL(18, 2))

    GarmentInstruction = relationship('GarmentInstruction')
    OrderGarment = relationship('OrderGarment')
    Order = relationship('Order')


class OrderIssue(db.Model):
    """
    This table contains the issues attached to corresponding order garments.
    Relationship(s):
    OrderId is a foreign key referencing OrderId in Orders table.
    OrderGarmentId is a foreign key referencing OrderGarmentId in OrderGarments table.
    IssueId is a foreign key referencing IssueId in GarmentIssues table.
    """
    __tablename__ = 'OrderIssues'

    OrderIssueId = db.Column(Integer, primary_key=True)
    OrderId = db.Column(ForeignKey('Orders.OrderId'), nullable=False)
    OrderGarmentId = db.Column(ForeignKey('OrderGarments.OrderGarmentId'), nullable=False)
    IssueId = db.Column(ForeignKey('GarmentIssues.IssueId'), nullable=False)
    IsDeleted = db.Column(BIT, nullable=False, server_default=text("((0))"))
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordLastUpdatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordVersion = db.Column(Integer, nullable=False, server_default=text("((0))"))

    GarmentIssue = relationship('GarmentIssue')
    OrderGarment = relationship('OrderGarment')
    Order = relationship('Order')


class OrderPhoto(db.Model):
    """
    This table contains the photo details attached to corresponding order garments.
    Relationship(s):
    OrderId is a foreign key referencing OrderId in Orders table.
    OrderGarmentId is a foreign key referencing OrderGarmentId in OrderGarments table.
    """
    __tablename__ = 'OrderPhotos'

    OrderPhotoId = db.Column(Integer, primary_key=True)
    OrderId = db.Column(ForeignKey('Orders.OrderId'), nullable=False)
    OrderGarmentId = db.Column(ForeignKey('OrderGarments.OrderGarmentId'), nullable=False)
    GarmentImage = db.Column(db.String(500, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    IsQC = db.Column(BIT, server_default=text("((0))"))
    IsVAS = db.Column(BIT, server_default=text("((0))"))
    IsNormal = db.Column(BIT, server_default=text("((1))"))
    IsDeleted = db.Column(BIT, nullable=False, server_default=text("((0))"))
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordLastUpdatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordVersion = db.Column(Integer, nullable=False, server_default=text("((0))"))

    OrderGarment = relationship('OrderGarment')
    Order = relationship('Order')


class OrderReviewReason(db.Model):
    """
    This master table contains the reasons available for a pickup/order review.
    """
    __tablename__ = 'OrderReviewReasons'

    OrderReviewReasonId = db.Column(Integer, primary_key=True)
    ReviewReason = db.Column(Unicode(500), nullable=False)
    IsDeleted = db.Column(BIT, nullable=False, server_default=text("((0))"))
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordLastUpdatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordVersion = db.Column(Integer, nullable=False, server_default=text("((0))"))


class OrderReview(db.Model):
    """
    This table contains the reviews of the orders/pickups.
    Relationship(s):
    OrderId is a foreign key referencing OrderId in Orders table.
    OrderReviewReasonId is a foreign key referencing OrderReviewReasonId in the OrderReviewReasons table.
    DUserId is a foreign key referencing DUserId in the Delivery Users table.
    """
    __tablename__ = 'OrderReviews'

    OrderReviewId = db.Column(Integer, primary_key=True)
    OrderId = db.Column(ForeignKey('Orders.OrderId'), nullable=False)
    OrderReviewReasonId = db.Column(ForeignKey('OrderReviewReasons.OrderReviewReasonId'))
    StarRating = db.Column(Integer, nullable=False)
    Remarks = db.Column(db.String(500, 'SQL_Latin1_General_CP1_CI_AS'))
    DUserId = db.Column(ForeignKey('DeliveryUsers.DUserId'), nullable=False)
    IsDeleted = db.Column(BIT, nullable=False, server_default=text("((0))"))
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordLastUpdatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordVersion = db.Column(Integer, nullable=False, server_default=text("((0))"))

    DeliveryUser = relationship('DeliveryUser')
    Order = relationship('Order')
    OrderReviewReason = relationship('OrderReviewReason')


class DeliveryUser(db.Model):
    """
    This master table contains the delivery/pickup users details.
    Relationship(s):
    AddedBy is a foreign key referencing SUserId in StoreUsers table.
    ModifiedBy is a foreign key referencing SUserId in StoreUsers table.
    """
    __tablename__ = 'DeliveryUsers'

    DUserId = db.Column(Integer, primary_key=True)
    POSUserId = db.Column(Integer)
    POSUsername = db.Column(db.String(100, 'SQL_Latin1_General_CP1_CI_AS'))
    UserName = db.Column(db.String(500, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    MobileNo = db.Column(db.String(20, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    Password = db.Column(db.String(50, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    EmailId = db.Column(db.String(500, 'SQL_Latin1_General_CP1_CI_AS'))
    Photo = db.Column(db.String(500, 'SQL_Latin1_General_CP1_CI_AS'))
    RegisteredDate = db.Column(db.DateTime, nullable=False)
    IsActive = db.Column(BIT, nullable=False, server_default=text("((1))"))
    IsDeleted = db.Column(BIT, nullable=False, server_default=text("((0))"))
    AddedBy = db.Column(ForeignKey('StoreUsers.SUserId'))
    ModifiedBy = db.Column(ForeignKey('StoreUsers.SUserId'))
    RemovedBy = db.Column(ForeignKey('StoreUsers.SUserId'))
    PartialPaymentPermission = db.Column(BIT, server_default=text("((0))"))
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordLastUpdatedDate = db.Column(db.DateTime)
    RecordVersion = db.Column(Integer, nullable=False, server_default=text("((0))"))
    DUserImage = db.Column(db.String(4000, 'SQL_Latin1_General_CP1_CI_AS'))
    ReschedulePickupPermission = db.Column(BIT, server_default=text("((0))"))
    CancellPickupPermission = db.Column(BIT, server_default=text("((0))"))
    DeliveryChargePermission = db.Column(BIT, server_default=text("((0))"))
    DeliveryWithoutOTPPermission = db.Column(BIT, server_default=text("((0))"))
    DeliverWithoutPaymentPermission = db.Column(BIT, server_default=text("((0))"))
    StoreUser = relationship('StoreUser', primaryjoin='DeliveryUser.AddedBy == StoreUser.SUserId')
    StoreUser1 = relationship('StoreUser', primaryjoin='DeliveryUser.ModifiedBy == StoreUser.SUserId')
    StoreUser2 = relationship('StoreUser', primaryjoin='DeliveryUser.RemovedBy == StoreUser.SUserId')


class DeliveryUserLogin(db.Model):
    """
    This table contains the login information for delivery users.
    Relationship(s):
    DUserId is a foreign key referencing DUserId in DeliveryUsers table.
    """
    __tablename__ = 'DeliveryUserLogins'
    # Edited by MMM
    FcmToken = db.Column(db.String(255, 'SQL_Latin1_General_CP1_CI_AS'))
    AppVersion = db.Column(db.String(255, 'SQL_Latin1_General_CP1_CI_AS'))
    BuildNumber = db.Column(db.Integer())
    # Edited by MMM
    DUserLoginId = db.Column(Integer, primary_key=True)
    DUserId = db.Column(ForeignKey('DeliveryUsers.DUserId'), nullable=False)
    LoginTime = db.Column(db.DateTime, nullable=False)
    AuthKey = db.Column(db.String(200, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    AuthKeyExpiry = db.Column(BIT, nullable=False, server_default=text("((0))"))
    LastAccessTime = db.Column(db.DateTime, nullable=False)
    IsActive = db.Column(BIT, nullable=False, server_default=text("((1))"))
    DeviceType = db.Column(CHAR(1, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    DeviceIP = db.Column(db.String(50, 'SQL_Latin1_General_CP1_CI_AS'))
    Browser = db.Column(db.String(80, 'SQL_Latin1_General_CP1_CI_AS'))
    Platform = db.Column(db.String(80, 'SQL_Latin1_General_CP1_CI_AS'))
    Language = db.Column(db.String(80, 'SQL_Latin1_General_CP1_CI_AS'))
    UAString = db.Column(db.String(200, 'SQL_Latin1_General_CP1_CI_AS'))
    UAVersion = db.Column(db.String(30, 'SQL_Latin1_General_CP1_CI_AS'))
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordLastUpdatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordVersion = db.Column(Integer, nullable=False, server_default=text("((0))"))

    DeliveryUser = relationship('DeliveryUser')


class DeliveryUserPassword(db.Model):
    """
    This table contains the password log of the delivery users.
    Relationship(s):
    DUserId is a foreign key referencing DUserId in DeliveryUsers table.
    """
    __tablename__ = 'DeliveryUserPasswords'

    DUserPasswordId = db.Column(Integer, primary_key=True)
    DUserId = db.Column(ForeignKey('DeliveryUsers.DUserId'), nullable=False)
    Password = db.Column(db.String(50, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordVersion = db.Column(Integer, nullable=False, server_default=text("((0))"))

    DeliveryUser = relationship('DeliveryUser')


class DeliveryUserBranch(db.Model):
    """
    This table contains the branch codes of a delivery user.
    Relationship(s):
    DUserId is a foreign key referencing DUserId in DeliveryUsers table.
    AddedBy is a foreign key referencing SUserId in StoreUsers table.
    BranchCode is a foreign key referencing BranchCode in Branches table.
    """
    __tablename__ = 'DeliveryUserBranches'

    DUserBranchId = db.Column(Integer, primary_key=True)
    DUserId = db.Column(ForeignKey('DeliveryUsers.DUserId'), nullable=False)
    POSUserId = db.Column(Integer)
    POSUsername = db.Column(db.String(100, 'SQL_Latin1_General_CP1_CI_AS'))
    BranchCode = db.Column(ForeignKey('Branches.BranchCode'), nullable=False)
    AddedBy = db.Column(ForeignKey('StoreUsers.SUserId'))
    IsDeleted = db.Column(BIT, nullable=False, server_default=text("((0))"))
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordLastUpdatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordVersion = db.Column(Integer, nullable=False, server_default=text("((0))"))
    IsDefaultBranch = db.Column(BIT, nullable=False, server_default=text("((0))"))

    Branch = relationship('Branch')
    DeliveryUser = relationship('DeliveryUser')
    StoreUser = relationship('StoreUser')


class DeliveryUserGPSLog(db.Model):
    """
    This table contains the GPS position logs of the delivery user.
    Relationship(s):
    DUserId is a foreign key referencing DUserId in DeliveryUsers table.
    """
    __tablename__ = 'DeliveryUserGPSLogs'

    Id = db.Column(Integer, primary_key=True)
    DUserId = db.Column(ForeignKey('DeliveryUsers.DUserId'), nullable=False)
    Lat = db.Column(DECIMAL(13, 10), nullable=False)
    Long = db.Column(DECIMAL(13, 10), nullable=False)
    IsDeleted = db.Column(BIT, nullable=False, server_default=text("((0))"))
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordLastUpdatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordVersion = db.Column(Integer, nullable=False, server_default=text("((0))"))

    DeliveryUser = relationship('DeliveryUser')


class DeliveryUserAttendance(db.Model):
    """
    This table contains the daily attendance logs of the delivery user.
    Relationship(s):
    DUserId is a foreign key referencing DUserId in DeliveryUsers table.
    """
    __tablename__ = 'DeliveryUserAttendance'

    AttendanceId = db.Column(Integer, primary_key=True)
    DUserId = db.Column(ForeignKey('DeliveryUsers.DUserId'), nullable=False)
    Date = db.Column(Date, nullable=False)
    ClockInTime = db.Column(Time, nullable=False)
    ClockInLat = db.Column(DECIMAL(13, 10))
    ClockInLong = db.Column(DECIMAL(13, 10))
    ClockOutTime = db.Column(Time)
    ClockOutLat = db.Column(DECIMAL(13, 10))
    ClockOutLong = db.Column(DECIMAL(13, 10))
    IsDeleted = db.Column(BIT, nullable=False, server_default=text("((0))"))
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordLastUpdatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordVersion = db.Column(Integer, nullable=False, server_default=text("((0))"))

    DeliveryUser = relationship('DeliveryUser')


class OTP(db.Model):
    """
    This table contains all the generated OTPs and corresponding mobile number and result from the SMS vendor.
    Relationship(s):
    SMSLog is a foreign key referencing Id in SMSLogs table.
    """
    __tablename__ = 'OTPs'

    OTPId = db.Column(Integer, primary_key=True)
    OTP = db.Column(Integer, nullable=False)
    MobileNumber = db.Column(db.String(20, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    Type = db.Column(db.String(50, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    Person = db.Column(db.String(100, 'SQL_Latin1_General_CP1_CI_AS'))
    IsVerified = db.Column(BIT, nullable=False, server_default=text("((0))"))
    SMSLog = db.Column(ForeignKey('SMSLogs.Id'))
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))

    SMSLog1 = relationship('SMSLog')


class DeliveryRequest(db.Model):
    """
    This table contains the all the pending delivery requests. Once all the garments from an order comes ready for delivery or,
    customer request for a partial delivery, this table will have an entry for that particular order id.

    Relationship(s):
    BranchCode is a foreign key referencing BranchCode in Branches table.
    CustAddressId is a foreign key referencing CustAddressId in CustomerAddress table.
    DeliveryTimeSlotId is a foreign key referencing PickupTimeSlotId in PickupTimeSlots table.
    OrderId is a foreign key referencing OrderId in Orders table.
    CustomerId is a foreign key referencing CustomerId in Customers table.
    DUserId is a foreign key referencing DUserId in DeliveryUsers table.
    CancelledStoreUser is a foreign key referencing SUserId in StoreUsers table.
    CreatedStoreUser is a foreign key referencing SUserId in StoreUsers table.
    AssignedStoreUser is a foreign key referencing SUserId in StoreUsers table.
    """
    __tablename__ = 'DeliveryRequests'

    DeliveryRequestId = db.Column(Integer, primary_key=True)
    CustomerId = db.Column(ForeignKey('Customers.CustomerId'), nullable=False)
    DeliveryDate = db.Column(db.DateTime, nullable=False)
    DeliveryTimeSlotId = db.Column(ForeignKey('FabPickupTimeSlots.PickupTimeSlotId'))
    TimeSlotFrom = db.Column(Time)
    TimeSlotTo = db.Column(Time)
    BranchCode = db.Column(ForeignKey('Branches.BranchCode'), nullable=False)
    CustAddressId = db.Column(ForeignKey('CustomerAddress.CustAddressId'), nullable=False)
    BookingId = db.Column(db.String(200, 'SQL_Latin1_General_CP1_CI_AS'))
    OrderId = db.Column(ForeignKey('Orders.OrderId'), nullable=False)
    IsPartial = db.Column(BIT, nullable=False, server_default=text("((0))"))
    DUserId = db.Column(ForeignKey('DeliveryUsers.DUserId'))
    IsDeleted = db.Column(Integer, nullable=False, server_default=text("((0))"))
    WalkIn = db.Column(BIT, nullable=True, server_default=text("((0))"))
    CancelledStoreUser = db.Column(ForeignKey('StoreUsers.SUserId'))
    CancelledDate = db.Column(db.DateTime)
    CreatedStoreUser = db.Column(ForeignKey('StoreUsers.SUserId'))
    AssignedStoreUser = db.Column(ForeignKey('StoreUsers.SUserId'))
    AssignedDate = db.Column(db.DateTime)
    CompletedDate = db.Column(db.DateTime)
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordLastUpdatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordVersion = db.Column(Integer, nullable=False, server_default=text("((0))"))
    CustomerPreferredDate = db.Column(db.DateTime)
    CustomerPreferredTimeSlot = db.Column(ForeignKey('CustomerTimeSlots.TimeSlotId'))
    InsertedBy = db.Column(db.String(100, 'SQL_Latin1_General_CP1_CI_AS'))
    CompletedBy = db.Column(Integer)
    TRNNo = db.Column(db.String(100, 'SQL_Latin1_General_CP1_CI_AS'))
    IsDeliverdFromFabricare = db.Column(BIT, nullable=False, server_default=text("((0))"))
    CustLat = db.Column(Float(53))
    CustLong = db.Column(Float(53))

    StoreUser = relationship('StoreUser', primaryjoin='DeliveryRequest.AssignedStoreUser == StoreUser.SUserId')
    Branch = relationship('Branch')
    # Edited by MMM
    CustomerTimeSlot = relationship('CustomerTimeSlot')
    # Edited by MMM
    StoreUser1 = relationship('StoreUser', primaryjoin='DeliveryRequest.CancelledStoreUser == StoreUser.SUserId')
    StoreUser2 = relationship('StoreUser', primaryjoin='DeliveryRequest.CreatedStoreUser == StoreUser.SUserId')
    CustomerAddres = relationship('CustomerAddres')
    Customer = relationship('Customer')
    DeliveryUser = relationship('DeliveryUser')
    FabPickupTimeSlots = relationship('FabPickupTimeSlots')
    Order = relationship('Order')

    ReschuduleStatus = db.Column(Integer)
    ReschuduleDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    ReschuduleBy = db.Column(Integer)
    ReschuduleAddressId = db.Column(Integer)
    ReschuduleModifiedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    ReschuduleTimeSlotId = db.Column(Integer)
    ReschuduleTimeSlotFrom = db.Column(Time)
    ReschuduleTimeSlotTo = db.Column(Time)


class Delivery(db.Model):
    """
    This table will have the final delivery detail of an order.

    Relationship(s):
    BranchCode is a foreign key referencing BranchCode in Branches table.
    DeliveryRequestId is a foreign key referencing DeliveryRequestId in DeliveryRequests table.
    PickupAddressId is a foreign key referencing PickupAddressId in DeliveryRequests table.
    DeliveryAddressId is a foreign key referencing DeliveryAddressId in CustomerAddress table.
    DUserId is a foreign key referencing DUserId in DeliveryUsers table.
    CustomerId is a foreign key referencing CustomerId in Customers table.
    OrderId is a foreign key referencing OrderId in Orders table.
    """
    __tablename__ = 'Deliveries'

    DeliveryId = db.Column(Integer, primary_key=True)
    EGRN = db.Column(db.String(50, 'SQL_Latin1_General_CP1_CI_AS'))
    CustomerId = db.Column(ForeignKey('Customers.CustomerId'), nullable=False)
    BranchCode = db.Column(ForeignKey('Branches.BranchCode'), nullable=False)
    DeliveryRequestId = db.Column(ForeignKey('DeliveryRequests.DeliveryRequestId'), nullable=False)
    OrderId = db.Column(ForeignKey('Orders.OrderId'), nullable=False)
    BookingId = db.Column(db.String(200, 'SQL_Latin1_General_CP1_CI_AS'))
    PickupAddressId = db.Column(ForeignKey('CustomerAddress.CustAddressId'), nullable=False)
    DeliveryAddressId = db.Column(ForeignKey('CustomerAddress.CustAddressId'), nullable=False)
    DeliveryDate = db.Column(db.DateTime, nullable=False)
    DUserId = db.Column(ForeignKey('DeliveryUsers.DUserId'))
    Remarks = db.Column(db.String(500, 'SQL_Latin1_General_CP1_CI_AS'))
    IsActive = db.Column(BIT, nullable=False, server_default=text("((0))"))
    # This Lat & Long is using for saving the geo-location while making the delivery.
    Lat = db.Column(DECIMAL(13, 10))
    Long = db.Column(DECIMAL(13, 10))
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordLastUpdatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordVersion = db.Column(Integer, nullable=False, server_default=text("((0))"))

    PaymentStatus = db.Column(db.String(500, 'SQL_Latin1_General_CP1_CI_AS'))
    DeliveryWithoutOtp = db.Column(BIT, nullable=False, server_default=text("((0))"))
    # DeliveryWithoutPayment = db.Column(BIT, nullable=False, server_default=text("((0))"))
    PaymentFlag = db.Column(Integer, nullable=False, server_default=text("((0))"))
    DeliverWithoutPayment = db.Column(BIT, nullable=False, server_default=text("0"))
    PaymentDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    Activity_Status = db.Column(Integer, nullable=False, server_default=text("((0))"))
    PayableAmount = db.Column(DECIMAL(precision=18, scale=2))

    DeliveryWithoutOTP = db.Column(BIT, nullable=False, server_default=text("((0))"))
    PaymentStatus = db.Column(db.String(500, 'SQL_Latin1_General_CP1_CI_AS'))
    DeliverWithoutPayment = db.Column(BIT, nullable=False, server_default=text("((0))"))
    PaymentDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    Activity_Status = db.Column(BIT, nullable=False, server_default=text("((0))"))
    ReasonId = db.Column(Integer, server_default=text("((0))"))
    Reasons = db.Column(db.String(500, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)

    CollectionAssignedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    CollectionTimeSlotId = db.Column(Integer, server_default=text("((0))"))
    CollectionTimeSlotFrom = db.Column(db.String(50, 'SQL_Latin1_General_CP1_CI_AS'))
    CollectionTimeSlotTo = db.Column(db.String(50, 'SQL_Latin1_General_CP1_CI_AS'))
    CollectionAssignedBY = db.Column(Integer, server_default=text("((0))"))
    CollectionAssignedTo = db.Column(Integer, server_default=text("((0))"))
    inlocation = db.Column(db.String(25, 'SQL_Latin1_General_CP1_CI_AS'))
    distance = db.Column(db.String(50, 'SQL_Latin1_General_CP1_CI_AS'))
    store_distance = db.Column(db.String(50, 'SQL_Latin1_General_CP1_CI_AS'))
    PartialStatus = db.Column(Integer, nullable=False, server_default=text("((0))"))
    TRNNo = db.Column(db.String(100, 'SQL_Latin1_General_CP1_CI_AS'))

    Branch = relationship('Branch')
    Customer = relationship('Customer')
    DeliveryUser = relationship('DeliveryUser')
    CustomerAddres = relationship('CustomerAddres',
                                  primaryjoin='Delivery.DeliveryAddressId == CustomerAddres.CustAddressId')
    DeliveryRequest = relationship('DeliveryRequest')
    Order = relationship('Order')
    CustomerAddres1 = relationship('CustomerAddres',
                                   primaryjoin='Delivery.PickupAddressId == CustomerAddres.CustAddressId')


class StoreUser(db.Model):
    """
    This master table contains the store admin users details.
    Relationship(s):
    BranchCode is a foreign key referencing BranchCode in Branches table.
    BranchCode2 is a foreign key referencing BranchCode in Branches table.
    BranchCode3 is a foreign key referencing BranchCode in Branches table.
    """

    __tablename__ = 'StoreUsers'

    SUserId = db.Column(Integer, primary_key=True)
    UserName = db.Column(db.String(500, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    MobileNo = db.Column(db.String(20, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    Password = db.Column(db.String(50, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    EmailId = db.Column(db.String(500, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    BranchCode = db.Column(ForeignKey('Branches.BranchCode'), nullable=False)
    BranchCode2 = db.Column(ForeignKey('Branches.BranchCode'))
    BranchCode3 = db.Column(ForeignKey('Branches.BranchCode'))
    Photo = db.Column(db.String(500, 'SQL_Latin1_General_CP1_CI_AS'))
    RegisteredDate = db.Column(db.DateTime, nullable=False)
    IsAdmin = db.Column(BIT, nullable=False, server_default=text("((0))"))
    IsZIC = db.Column(BIT, nullable=False, server_default=text("((0))"))
    IsActive = db.Column(BIT, nullable=False, server_default=text("((1))"))
    IsDeleted = db.Column(BIT, nullable=False, server_default=text("((0))"))
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordLastUpdatedDate = db.Column(db.DateTime)
    RecordVersion = db.Column(Integer, nullable=False, server_default=text("((0))"))
    CancellPickupPermission = db.Column(BIT, server_default=text("((0))"))
    ReschedulePickupPermission = db.Column(BIT, server_default=text("((0))"))
    BranchChangePermission = db.Column(BIT, server_default=text("((0))"))
    AddedBy = db.Column(ForeignKey('StoreUsers.SUserId'))
    ModifiedBy = db.Column(ForeignKey('StoreUsers.SUserId'))

    Branch = relationship('Branch', primaryjoin='StoreUser.BranchCode == Branch.BranchCode')
    Branch1 = relationship('Branch', primaryjoin='StoreUser.BranchCode2 == Branch.BranchCode')
    Branch2 = relationship('Branch', primaryjoin='StoreUser.BranchCode3 == Branch.BranchCode')


class StoreUserLogin(db.Model):
    """
    This table contains the login information for store admin users.
    Relationship(s):
    SUserId is a foreign key referencing SUserId in StoreUsers table.
    """
    __tablename__ = 'StoreUserLogins'

    SUserLoginId = db.Column(Integer, primary_key=True)
    SUserId = db.Column(ForeignKey('StoreUsers.SUserId'), nullable=False)
    LoginTime = db.Column(db.DateTime, nullable=False)
    AuthKey = db.Column(db.String(200, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    AuthKeyExpiry = db.Column(BIT, nullable=False)
    LastAccessTime = db.Column(db.DateTime, nullable=False)
    IsActive = db.Column(BIT, nullable=False)
    DeviceType = db.Column(CHAR(1, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    DeviceIP = db.Column(db.String(50, 'SQL_Latin1_General_CP1_CI_AS'))
    Browser = db.Column(db.String(80, 'SQL_Latin1_General_CP1_CI_AS'))
    Platform = db.Column(db.String(80, 'SQL_Latin1_General_CP1_CI_AS'))
    Language = db.Column(db.String(80, 'SQL_Latin1_General_CP1_CI_AS'))
    UAString = db.Column(db.String(200, 'SQL_Latin1_General_CP1_CI_AS'))
    UAVersion = db.Column(db.String(30, 'SQL_Latin1_General_CP1_CI_AS'))
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordLastUpdatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordVersion = db.Column(Integer, nullable=False)

    StoreUser = relationship('StoreUser')


class StoreUserBranch(db.Model):
    """
    This table contains the branch codes of a store user.
    Relationship(s):
    SUserId is a foreign key referencing SUserId in StoreUsers table.
    BranchCode is a foreign key referencing BranchCode in Branches table.
    """
    __tablename__ = 'StoreUserBranches'

    SUserBranchId = db.Column(Integer, primary_key=True)
    SUserId = db.Column(ForeignKey('StoreUsers.SUserId'), nullable=False)
    BranchCode = db.Column(ForeignKey('Branches.BranchCode'), nullable=False)
    IsDeleted = db.Column(BIT, nullable=False, server_default=text("((0))"))
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordLastUpdatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordVersion = db.Column(Integer, nullable=False, server_default=text("((0))"))

    Branch = relationship('Branch')
    StoreUser = relationship('StoreUser')


class StoreUserAttendance(db.Model):
    """
    This table contains the daily attendance logs of the store user.
    Relationship(s):
    SUserId is a foreign key referencing SUserId in StoreUsers table.
    """
    __tablename__ = 'StoreUserAttendance'

    AttendanceId = db.Column(Integer, primary_key=True)
    SUserId = db.Column(ForeignKey('StoreUsers.SUserId'), nullable=False)
    Date = db.Column(Date, nullable=False)
    ClockInTime = db.Column(Time, nullable=False)
    ClockOutTime = db.Column(Time)
    IsDeleted = db.Column(BIT, nullable=False, server_default=text("((0))"))
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordLastUpdatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordVersion = db.Column(Integer, nullable=False, server_default=text("((0))"))

    StoreUser = relationship('StoreUser')


class MSSWeeklyOff(db.Model):
    """
    This table contains the weekly off days configuration of the MSS.
    i.e. 0 is for Sunday, ...6 for Saturday.
    Relationship(s):
    StateCode is a foreign key referencing StateCode in States table.
    """
    __tablename__ = 'MSSWeeklyOff'

    Id = db.Column(Integer, primary_key=True)
    StateCode = db.Column(ForeignKey('States.StateCode'), nullable=False)
    WeeklyOff = db.Column(Integer)

    State = relationship('State')


class DeliveryDateEstimator(db.Model):
    """
    This table contains the days require to service a garment.
    Relationship(s):
    GarmentId is a foreign key referencing GarmentId in Garments table.
    ServiceTatId is a foreign key referencing ServiceTatId in ServiceTats table.
    ServiceTypeId is a foreign key referencing ServiceTypeId in ServiceTypes table.
    BranchCode is a foreign key referencing BranchCode in Branches table.
    """
    __tablename__ = 'DeliveryDateEstimator'

    Id = db.Column(Integer, primary_key=True)
    GarmentId = db.Column(ForeignKey('Garments.GarmentId'), nullable=False)
    BranchCode = db.Column(ForeignKey('Branches.BranchCode'), nullable=False)
    ServiceTatId = db.Column(ForeignKey('ServiceTats.ServiceTatId'), nullable=False)
    ServiceTypeId = db.Column(ForeignKey('ServiceTypes.ServiceTypeId'))
    Time = db.Column(Integer, nullable=False)
    VASId = db.Column(Integer)
    IsActive = db.Column(BIT, nullable=False, server_default=text("((1))"))
    IsDeleted = db.Column(BIT, nullable=False, server_default=text("((0))"))
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordLastUpdatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordVersion = db.Column(Integer, nullable=False, server_default=text("((0))"))

    Branch = relationship('Branch')
    Garment = relationship('Garment')
    ServiceTat = relationship('ServiceTat')
    ServiceType = relationship('ServiceType')


class QCInfo(db.Model):
    """
    This table contains the QC details of the order garments.
    """
    __tablename__ = 'QCInfo'

    QCID = db.Column(UNIQUEIDENTIFIER, primary_key=True)
    POSOrderGarmentID = db.Column(UNIQUEIDENTIFIER, nullable=False)
    Status = db.Column(Integer, nullable=False)
    Reason = db.Column(Integer)
    Remark = db.Column(db.String(500, 'SQL_Latin1_General_CP1_CI_AS'))
    PostedDateTime = db.Column(db.DateTime, nullable=False)
    PostedBy = db.Column(Integer, nullable=False)
    CreatedOn = db.Column(db.DateTime)
    Photo = db.Column(db.String(500, 'SQL_Latin1_General_CP1_CI_AS'))
    Image1 = db.Column(db.String(2000, 'SQL_Latin1_General_CP1_CI_AS'))
    Image2 = db.Column(db.String(2000, 'SQL_Latin1_General_CP1_CI_AS'))
    Image3 = db.Column(db.String(2000, 'SQL_Latin1_General_CP1_CI_AS'))
    CustomerCode = db.Column(db.String(50, 'SQL_Latin1_General_CP1_CI_AS'))
    IsActive = db.Column(BIT, nullable=False, server_default=text("((1))"))
    IsDeleted = db.Column(BIT, nullable=False, server_default=text("((0))"))
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordLastUpdatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordVersion = db.Column(Integer, nullable=False, server_default=text("((0))"))


class DeliveryReviewReason(db.Model):
    """
    This master table contains the reasons available for a delivery review.
    """
    __tablename__ = 'DeliveryReviewReasons'

    DeliveryReviewReasonId = db.Column(Integer, primary_key=True)
    ReviewReason = db.Column(Unicode(500), nullable=False)
    IsDeleted = db.Column(BIT, nullable=False, server_default=text("((0))"))
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordLastUpdatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordVersion = db.Column(Integer, nullable=False, server_default=text("((0))"))


class DeliveryReview(db.Model):
    """
    This table contains the reviews of the deliveries.
    Relationship(s):
    OrderId is a foreign key referencing OrderId in Orders table.
    DeliveryReviewReasonId is a foreign key referencing DeliveryReviewReasonId in the DeliveryReviewReasons table.
    DUserId is a foreign key referencing DUserId in the Delivery Users table.
    """
    __tablename__ = 'DeliveryReviews'

    DeliveryReviewId = db.Column(Integer, primary_key=True)
    OrderId = db.Column(ForeignKey('Orders.OrderId'), nullable=False)
    DeliveryReviewReasonId = db.Column(ForeignKey('DeliveryReviewReasons.DeliveryReviewReasonId'))
    StarRating = db.Column(Integer, nullable=False)
    Remarks = db.Column(db.String(500, 'SQL_Latin1_General_CP1_CI_AS'))
    DUserId = db.Column(ForeignKey('DeliveryUsers.DUserId'), nullable=False)
    IsDeleted = db.Column(BIT, nullable=False, server_default=text("((0))"))
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordLastUpdatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordVersion = db.Column(Integer, nullable=False, server_default=text("((0))"))

    DeliveryUser = relationship('DeliveryUser')
    DeliveryReviewReason = relationship('DeliveryReviewReason')
    Order = relationship('Order')


class ComplaintType(db.Model):
    """
    This master table contains all the possible complaint types that can be passed to the Ameyo ticketing service.
    """
    __tablename__ = 'ComplaintTypes'

    Id = db.Column(Integer, primary_key=True)
    DeptName = db.Column(db.String(100, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    ComplaintTypeName = db.Column(db.String(100, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    ComplaintTypeValue = db.Column(db.String(200, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    BrandCode = db.Column(db.String(50, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    IsDeleted = db.Column(BIT, nullable=False, server_default=text("((0))"))
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordLastUpdatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordVersion = db.Column(Integer, nullable=False, server_default=text("((0))"))


class Complaint(db.Model):
    """
    This table contains the complaints that are registered with the Ameyo ticketing service.
    Relationship(s):
    BranchCode is a foreign key referencing BranchCode in Branches table.
    CityCode is a foreign key referencing CityCode in Cities table.
    StateCode is a foreign key referencing StateCode in State table.
    """
    __tablename__ = 'Complaints'

    Id = db.Column(Integer, primary_key=True)
    AmeyoTicketId = db.Column(db.String(50, 'SQL_Latin1_General_CP1_CI_AS'))
    CRMComplaintId = db.Column(Integer)
    JFSLTicketId = db.Column(db.String(100, 'SQL_Latin1_General_CP1_CI_AS'))
    TicketSubject = db.Column(db.String(200, 'SQL_Latin1_General_CP1_CI_AS'))
    AmeyoTicketSourceType = db.Column(db.String(50, 'SQL_Latin1_General_CP1_CI_AS'))
    AmeyoTicketStatus = db.Column(db.String(100, 'SQL_Latin1_General_CP1_CI_AS'))
    CRMComplaintStatus = db.Column(db.String(100, 'SQL_Latin1_General_CP1_CI_AS'))
    ClientId = db.Column(db.String(50, 'SQL_Latin1_General_CP1_CI_AS'))
    MobileNo = db.Column(db.String(20, 'SQL_Latin1_General_CP1_CI_AS'))
    ComplaintDate = db.Column(db.DateTime)
    BranchCode = db.Column(ForeignKey('Branches.BranchCode'))
    BrandCode = db.Column(db.String(50, 'SQL_Latin1_General_CP1_CI_AS'))
    ComplaintType = db.Column(db.String(100, 'SQL_Latin1_General_CP1_CI_AS'))
    EGRN = db.Column(db.String(50, 'SQL_Latin1_General_CP1_CI_AS'))
    ComplaintDesc = db.Column(db.String(4000, 'SQL_Latin1_General_CP1_CI_AS'))
    AssignedDept = db.Column(db.String(100, 'SQL_Latin1_General_CP1_CI_AS'))
    TagId = db.Column(db.String(50, 'SQL_Latin1_General_CP1_CI_AS'))
    CityCode = db.Column(ForeignKey('Cities.CityCode'))
    StateCode = db.Column(ForeignKey('States.StateCode'))
    CampaignId = db.Column(db.String(2, 'SQL_Latin1_General_CP1_CI_AS'))
    QueueId = db.Column(db.String(2, 'SQL_Latin1_General_CP1_CI_AS'))
    AssignedUserId = db.Column(db.String(50, 'SQL_Latin1_General_CP1_CI_AS'))
    IsDeleted = db.Column(BIT, nullable=False, server_default=text("((0))"))
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordLastUpdatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordVersion = db.Column(Integer, nullable=False, server_default=text("((0))"))

    Branch = relationship('Branch')
    City = relationship('City')
    State = relationship('State')


class TransactionInfo(db.Model):
    """
    First of the two payment tables. This table contains the initial datas for a transaction.
    """
    __tablename__ = 'TransactionInfo'

    Id = db.Column(Integer, primary_key=True)
    CustomerCode = db.Column(Unicode(250))
    TransactionId = db.Column(Unicode(250))
    TransactionDate = db.Column(db.DateTime)
    EGRNNo = db.Column(Unicode(250))
    DCNo = db.Column(Unicode(250))
    ServiceCharge = db.Column(DECIMAL(18, 2))
    ServiceSGST = db.Column(DECIMAL(18, 2))
    ServiceCGST = db.Column(DECIMAL(18, 2))
    ServiceGST = db.Column(DECIMAL(18, 2))
    FinalServiceAmount = db.Column(DECIMAL(18, 2))
    ProductCharge = db.Column(DECIMAL(18, 2))
    ProductSGST = db.Column(DECIMAL(18, 2))
    ProductCGST = db.Column(DECIMAL(18, 2))
    ProductGST = db.Column(DECIMAL(18, 2))
    FinalProductAmount = db.Column(DECIMAL(18, 2))
    TransactionCarryBagId = db.Column(Unicode(250))
    UsedCompensationCoupons = db.Column(Unicode(250))
    DiscountAmount = db.Column(DECIMAL(18, 2))
    TotalPayableAmount = db.Column(DECIMAL(18, 2))
    RoundOff = db.Column(DECIMAL(18, 2))
    Status = db.Column(Integer, nullable=False, server_default=text("((0))"))
    PaymentId = db.Column(Unicode(500))
    PaymentSource = db.Column(Unicode(20))
    OrderGarmentIDs = db.Column(db.String(4000, 'SQL_Latin1_General_CP1_CI_AS'))
    RevisedBasicAmount = db.Column(DECIMAL(18, 2))
    RevisedRoundOff = db.Column(DECIMAL(18, 2))
    RevisedInvoiceAmount = db.Column(DECIMAL(18, 2))
    ProductBasicAmount = db.Column(DECIMAL(18, 2))
    ProductRoundOff = db.Column(DECIMAL(18, 2))
    ProductInvoiceAmount = db.Column(DECIMAL(18, 2))
    RevisedPayableAmount = db.Column(DECIMAL(18, 2))
    InvoiceDiscountCode = db.Column(Unicode(100))
    InvoiceDiscount = db.Column(DECIMAL(18, 2))
    Gateway = db.Column(Unicode(80))
    GarmentsCount = db.Column(Integer)
    ConsoleVerify = db.Column(TINYINT)
    ManualVerify = db.Column(TINYINT)
    VerifiedBy = db.Column(Unicode(100))
    VerificationDate = db.Column(db.DateTime)
    Loyaltypoints = db.Column(Integer)
    LoyaltyPointsRate = db.Column(DECIMAL(18, 2))
    LoyaltyPointsAmount = db.Column(DECIMAL(18, 2))
    AvailableLoyaltyPoints = db.Column(DECIMAL(18, 2))
    ERTransactionCode = db.Column(Unicode(60))
    InvoiceNo = db.Column(Unicode(30))
    PaymentFrom = db.Column(db.String(100, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)

    PaymentCompletedOn = db.Column(db.DateTime)
    PaymentCollectedBY = db.Column(ForeignKey('DeliveryUsers.DUserId'))

    DeliveryUser = relationship('DeliveryUser')


class TransactionPaymentInfo(db.Model):
    """
    Second table for the payment.
    Data coming from payment gateway is stored in this table as well as invoice number.
    """
    __tablename__ = 'TransactionPaymentInfo'

    Id = db.Column(Integer, primary_key=True)
    PaymentId = db.Column(Unicode(250))
    CreatedOn = db.Column(db.DateTime)
    TransactionId = db.Column(Unicode(250))
    PaymentMode = db.Column(Unicode(50))
    CardTransactionId = db.Column(Unicode(100))
    CouponCode = db.Column(Unicode(30))
    PaymentAmount = db.Column(DECIMAL(18, 2))
    RoundOff = db.Column(DECIMAL(18, 2))
    PaymentGatewayStatus = db.Column(Unicode(10))
    PaymentGatewayStatusDescription = db.Column(Unicode(200))
    InvoiceNo = db.Column(Unicode(100))
    Remarks = db.Column(Unicode(200))
    PgTransId = db.Column(Unicode(200))
    BranchCode = db.Column(Unicode(50))
    SettlementProcedure = db.Column(Unicode(40))
    IsERSync = db.Column(Integer)
    ManualSettlementDate = db.Column(db.DateTime)


class DeliveryRescheduleReason(db.Model):
    """
    This master table contains the predefined reasons for delivery reschedule.
    """
    __tablename__ = 'DeliveryRescheduleReasons'

    RescheduleReasonId = db.Column(Integer, primary_key=True)
    RescheduleReason = db.Column(Unicode(500), nullable=False)
    IsDeleted = db.Column(BIT, nullable=False, server_default=text("((0))"))
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordLastUpdatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordVersion = db.Column(Integer, nullable=False, server_default=text("((0))"))


class DeliveryReschedule(db.Model):
    """
    This table contains the reschedules made for corresponding delivery requests.
    Relationship(s):
    DeliveryRequestId is a foreign key referencing DeliveryRequestId in DeliveryRequests table.
    RescheduleReasonId is a foreign key referencing RescheduleReasonId in DeliveryRescheduleReasons table.
    DeliveryTimeSlotId is a foreign key referencing PickupTimeSlotId in PickupTimeSlots table.
    DUserId is a foreign key referencing DUserId in DeliveryUsers table.
    CustAddressId is a foreign key referencing CustAddressId in CustomerAddress table.
    RescheduledStoreUser is a foreign key referencing SUserId in StoreUsers table.
    AssignedStoreUser is a foreign key referencing SUserId in StoreUsers table.
    """
    __tablename__ = 'DeliveryReschedules'

    Id = db.Column(Integer, primary_key=True)
    DeliveryRequestId = db.Column(ForeignKey('DeliveryRequests.DeliveryRequestId'), nullable=False)
    RescheduleReasonId = db.Column(ForeignKey('DeliveryRescheduleReasons.RescheduleReasonId'))
    TimeSlotFrom = db.Column(Time)
    TimeSlotTo = db.Column(Time)
    RescheduledDate = db.Column(Date, nullable=False)
    DeliveryTimeSlotId = db.Column(ForeignKey('FabPickupTimeSlots.PickupTimeSlotId'), nullable=False)
    RescheduleRemarks = db.Column(db.String(500, 'SQL_Latin1_General_CP1_CI_AS'))
    DUserId = db.Column(ForeignKey('DeliveryUsers.DUserId'))
    CustAddressId = db.Column(ForeignKey('CustomerAddress.CustAddressId'), nullable=False)
    RescheduledBy = db.Column(db.String(2, 'SQL_Latin1_General_CP1_CI_AS'))
    RefId = db.Column(Integer)
    IsDeleted = db.Column(BIT, nullable=False, server_default=text("((0))"))
    CancelledDate = db.Column(db.DateTime)
    RescheduledStoreUser = db.Column(ForeignKey('StoreUsers.SUserId'))
    AssignedStoreUser = db.Column(ForeignKey('StoreUsers.SUserId'))
    AssignedDate = db.Column(db.DateTime)
    # This Lat & Long is using for saving the geo-location while rescheduling the delivery.
    Lat = db.Column(DECIMAL(13, 10))
    Long = db.Column(DECIMAL(13, 10))
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordLastUpdatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordVersion = db.Column(Integer, nullable=False, server_default=text("((0))"))
    CustomerPreferredTimeSlot = db.Column(ForeignKey('CustomerTimeSlots.TimeSlotId'))

    # Edited by MMM
    CustomerTimeSlot = relationship('CustomerTimeSlot')
    # Edited by MMM
    StoreUser = relationship('StoreUser', primaryjoin='DeliveryReschedule.AssignedStoreUser == StoreUser.SUserId')
    CustomerAddres = relationship('CustomerAddres')
    DeliveryUser = relationship('DeliveryUser')
    DeliveryRequest = relationship('DeliveryRequest')
    FabPickupTimeSlots = relationship('FabPickupTimeSlots')
    DeliveryRescheduleReason = relationship('DeliveryRescheduleReason')
    StoreUser1 = relationship('StoreUser', primaryjoin='DeliveryReschedule.RescheduledStoreUser == StoreUser.SUserId')


class DeliveryGarment(db.Model):
    """
    This table contains the ready for delivery garments for a delivery.
    Relationship(s):
    OrderGarmentId is a foreign key referencing OrderGarmentId in OrderGarments table.
    OrderId is a foreign key referencing OrderId in Orders table.
    DeliveryRequestId is a foreign key referencing DeliveryRequestId in the DeliveryRequests table.
    """
    __tablename__ = 'DeliveryGarments'

    DeliveryGarmentId = db.Column(Integer, primary_key=True)
    OrderGarmentId = db.Column(ForeignKey('OrderGarments.OrderGarmentId'), nullable=False)
    POSOrderGarmentId = db.Column(UNIQUEIDENTIFIER, nullable=False)
    OrderId = db.Column(ForeignKey('Orders.OrderId'), nullable=False)
    DeliveryRequestId = db.Column(ForeignKey('DeliveryRequests.DeliveryRequestId'))
    IsDeleted = db.Column(BIT, nullable=False, server_default=text("((0))"))
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordLastUpdatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordVersion = db.Column(Integer, nullable=False, server_default=text("((0))"))

    DeliveryRequest = relationship('DeliveryRequest')
    OrderGarment = relationship('OrderGarment')
    Order = relationship('Order')


class TravelLog(db.Model):
    """
    This table contains the travel history of the delivery user.
    Relationship(s):
    DUserId is a foreign key referencing DUserId in DeliveryUsers table.
    OrderId is a foreign key referencing OrderId in Orders table.
    DeliveryId is a foreign key referencing DeliveryId in Deliveries table.
    """
    __tablename__ = 'TravelLogs'

    TravelLogId = db.Column(Integer, primary_key=True)
    Activity = db.Column(db.String(50, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    DUserId = db.Column(ForeignKey('DeliveryUsers.DUserId'), nullable=False)
    OrderId = db.Column(ForeignKey('Orders.OrderId'))
    DeliveryId = db.Column(ForeignKey('Deliveries.DeliveryId'))
    Lat = db.Column(DECIMAL(13, 10), nullable=False)
    Long = db.Column(DECIMAL(13, 10), nullable=False)
    IsDeleted = db.Column(BIT, nullable=False, server_default=text("((0))"))
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordLastUpdatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordVersion = db.Column(Integer, nullable=False, server_default=text("((0))"))

    DeliveryUser = relationship('DeliveryUser')
    Delivery = relationship('Delivery')
    Order = relationship('Order')


class MessageTemplate(db.Model):
    """
    This table contains the predefined message templates.
    """
    __tablename__ = 'MessageTemplates'

    Id = db.Column(Integer, primary_key=True)
    Title = db.Column(db.String(50, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    MessageContent = db.Column(db.String(1000, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    IsDeleted = db.Column(BIT, nullable=False, server_default=text("((0))"))
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordLastUpdatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordVersion = db.Column(Integer, nullable=False, server_default=text("((0))"))
    Brand = db.Column(db.String(50, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)


class SMSLog(db.Model):
    """
    This table contains the SMS API service's logs.
    """
    __tablename__ = 'SMSLogs'
    # Edited By MMM
    CustomerId = db.Column(Integer)
    # Edited By MMM
    Id = db.Column(Integer, primary_key=True)
    MobileNumber = db.Column(db.String(20, 'SQL_Latin1_General_CP1_CI_AS'))
    APIRequest = db.Column(db.String(2000, 'SQL_Latin1_General_CP1_CI_AS'))
    APIResponse = db.Column(db.String(2000, 'SQL_Latin1_General_CP1_CI_AS'))
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))


class PartialCollection(db.Model):
    """
    This table contains the partial collection details.
    Relationship(s):
    DeliveryRequestId is a foreign key referencing DeliveryRequestId in DeliveryRequests table.
    OrderId is a foreign key referencing OrderId in Orders table.
    """
    __tablename__ = 'PartialCollections'

    Id = db.Column(Integer, primary_key=True)
    DeliveryRequestId = db.Column(ForeignKey('DeliveryRequests.DeliveryRequestId'), nullable=False)
    OrderId = db.Column(ForeignKey('Orders.OrderId'), nullable=False)
    EGRN = db.Column(db.String(50, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    PaymentMode = db.Column(db.String(100, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    CollectedAmount = db.Column(DECIMAL(18, 2), nullable=False)
    IsDeleted = db.Column(BIT, nullable=False, server_default=text("((0))"))
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordLastUpdatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordVersion = db.Column(Integer, nullable=False, server_default=text("((0))"))

    DeliveryRequest = relationship('DeliveryRequest')
    Order = relationship('Order')


class MessageLog(db.Model):
    """
    This table contains the waiting SMS logs sent to customers from the delivery app.
    Relationship(s):
    MessageTemplateId is a foreign key referencing Id in MessageTemplates table.
    PickupRequestId is a foreign key referencing PickupRequestId in PickupRequests table.
    DeliveryRequestId is a foreign key referencing DeliveryRequestId in DeliveryRequestId table.
    DUserId is a foreign key referencing DUserId in DeliveryUsers table.
    """
    __tablename__ = 'MessageLogs'

    Id = db.Column(Integer, primary_key=True)
    CustomerCode = db.Column(db.String(30, 'SQL_Latin1_General_CP1_CI_AS'))
    DUserId = db.Column(ForeignKey('DeliveryUsers.DUserId'))
    PickupRequestId = db.Column(ForeignKey('PickupRequests.PickupRequestId'))
    DeliveryRequestId = db.Column(ForeignKey('DeliveryRequests.DeliveryRequestId'))
    MessageTemplateId = db.Column(ForeignKey('MessageTemplates.Id'), nullable=False)
    MobileNo = db.Column(db.String(20, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    Lat = db.Column(DECIMAL(13, 10))
    Long = db.Column(DECIMAL(13, 10))
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordLastUpdatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordVersion = db.Column(Integer, nullable=False, server_default=text("((0))"))

    MessageTemplate = relationship('MessageTemplate')
    DeliveryRequest = relationship('DeliveryRequest')
    PickupRequest = relationship('PickupRequest')
    DeliveryUser = relationship('DeliveryUser')


class FabPickupTimeSlots(db.Model):
    """
    This master table contains the Timeslot details.
    """
    __tablename__ = 'FabPickupTimeSlots'

    PickupTimeSlotId = db.Column(Integer, primary_key=True)
    TimeSlot = db.Column(db.String(255, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    TimeSlotFrom = db.Column(Time)
    TimeSlotTo = db.Column(Time)
    IsActive = db.Column(BIT, server_default=text("((1))"))
    IsDeleted = db.Column(BIT, server_default=text("((0))"))


class ReasonTemplates(db.Model):
    """
       This master table contains the reasons.
       """
    __tablename__ = 'ReasonTemplates'

    Id = db.Column(Integer, primary_key=True)
    Title = db.Column(db.String(255, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    Description = db.Column(db.String(255, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    ReasonValue = db.Column(db.String(255, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordLastUpdatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))

    IsDeleted = db.Column(BIT, server_default=text("((0))"))


class PickupInstructions(db.Model):
    """
       This master table contains the reasons.
       """
    __tablename__ = 'PickupInstructions '

    PickupinstructionsId = db.Column(Integer, primary_key=True)
    Pickupinstructions = db.Column(db.String(255, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    PosId = db.Column(db.String(255, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    PickupinstructionsImage = db.Column(db.String(255, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    Category = db.Column(db.String(255, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordUpdatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    PickupInstructionDescription = db.Column(db.String(255, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)

    # IsDeleted = db.Column(BIT, server_default=text("((0))"))

