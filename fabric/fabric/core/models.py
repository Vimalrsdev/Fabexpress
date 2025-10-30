from fabric import db
from sqlalchemy import CHAR, DECIMAL, ForeignKey, Integer, text, Time, Date, Unicode
from sqlalchemy.dialects.mssql import BIT, UNIQUEIDENTIFIER
from sqlalchemy.orm import relationship
from fabric.modules.generic.classes import GetDict


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
    BranchAddress = db.Column(db.String(2000, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    PhoneNo = db.Column(db.String(100, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    AreaCode = db.Column(ForeignKey('Areas.AreaCode'), nullable=False)
    RouteCode = db.Column(db.String(50, 'SQL_Latin1_General_CP1_CI_AS'))
    Pincode = db.Column(db.String(10, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    BranchServiceTimeWeekDay = db.Column(db.String(50, 'SQL_Latin1_General_CP1_CI_AS'))
    BranchServiceTimeWeekend = db.Column(db.String(50, 'SQL_Latin1_General_CP1_CI_AS'))
    LatVal = db.Column(DECIMAL(13, 10), nullable=False)
    LongVal = db.Column(DECIMAL(13, 10), nullable=False)
    WeeklyOffDays = db.Column(Integer)
    IsActive = db.Column(BIT, nullable=False, server_default=text("((1))"))
    IsDeleted = db.Column(BIT, nullable=False, server_default=text("((0))"))
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordLastUpdatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordVersion = db.Column(Integer, nullable=False)

    Area = relationship('Area')


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
    GarmentPreference = db.Column(Integer, server_default=text("((0))"))
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
    LastSignInTime = db.Column(db.DateTime, nullable=False)
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
    LatVal = db.Column(DECIMAL(13, 10))
    LongVal = db.Column(DECIMAL(13, 10))
    IsActive = db.Column(BIT, nullable=False, server_default=text("((1))"))
    IsDeleted = db.Column(BIT, nullable=False, server_default=text("((0))"))
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordLastUpdatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordVersion = db.Column(Integer, nullable=False, server_default=text("((0))"))

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
    """
    __tablename__ = 'PickupRequests'

    PickupRequestId = db.Column(Integer, primary_key=True)
    CustomerId = db.Column(ForeignKey('Customers.CustomerId'), nullable=False)
    PickupDate = db.Column(db.DateTime, nullable=False)
    PickupTimeSlotId = db.Column(ForeignKey('PickupTimeSlots.PickupTimeSlotId'), nullable=False)
    TimeSlotFrom = db.Column(Time, nullable=False)
    TimeSlotTo = db.Column(Time, nullable=False)
    BranchCode = db.Column(ForeignKey('Branches.BranchCode'), nullable=False)
    CustAddressId = db.Column(ForeignKey('CustomerAddress.CustAddressId'), nullable=False)
    PickupSource = db.Column(db.String(50, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    DiscountCode = db.Column(db.String(50, 'SQL_Latin1_General_CP1_CI_AS'))
    CouponCode = db.Column(db.String(50, 'SQL_Latin1_General_CP1_CI_AS'))
    ApplyLoyalityPoints = db.Column(BIT, nullable=False, server_default=text("((0))"))
    BookingId = db.Column(db.String(200, 'SQL_Latin1_General_CP1_CI_AS'))
    PickupStatusId = db.Column(ForeignKey('PickupStatusCodes.PickupStatusId'), nullable=False)
    DUserId = db.Column(ForeignKey('DeliveryUsers.DUserId'))
    IsCancelled = db.Column(BIT, nullable=False, server_default=text("((0))"))
    CancelReasonId = db.Column(ForeignKey('PickupCancelReasons.CancelReasonId'))
    CancelledDate = db.Column(db.DateTime)
    CancelRemarks = db.Column(db.String(500, 'SQL_Latin1_General_CP1_CI_AS'))
    CancelledBy = db.Column(db.String(2, 'SQL_Latin1_General_CP1_CI_AS'))
    CancelledRefId = db.Column(Integer)
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordLastUpdatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordVersion = db.Column(Integer, nullable=False, server_default=text("((0))"))

    Branch = relationship('Branch')
    PickupCancelReason = relationship('PickupCancelReason')
    CustomerAddres = relationship('CustomerAddres')
    Customer = relationship('Customer')
    DeliveryUser = relationship('DeliveryUser')
    PickupStatusCode = relationship('PickupStatusCode')
    PickupTimeSlot = relationship('PickupTimeSlot')

    ServiceTat = relationship('ServiceTat')

    #Laji
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
    """
    __tablename__ = 'PickupReschedules'

    Id = db.Column(Integer, primary_key=True)
    PickupRequestId = db.Column(ForeignKey('PickupRequests.PickupRequestId'), nullable=False)
    RescheduleReasonId = db.Column(ForeignKey('PickupRescheduleReasons.RescheduleReasonId'), nullable=False)
    RescheduledDate = db.Column(Date, nullable=False)
    PickupTimeSlotId = db.Column(ForeignKey('PickupTimeSlots.PickupTimeSlotId'), nullable=False)
    RescheduleRemarks = db.Column(db.String(500, 'SQL_Latin1_General_CP1_CI_AS'))
    RescheduledBy = db.Column(db.String(2, 'SQL_Latin1_General_CP1_CI_AS'))
    RefId = db.Column(Integer)
    IsDeleted = db.Column(BIT, nullable=False, server_default=text("((0))"))
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordLastUpdatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordVersion = db.Column(Integer, nullable=False, server_default=text("((0))"))

    PickupRequest = relationship('PickupRequest')
    PickupTimeSlot = relationship('PickupTimeSlot')
    PickupRescheduleReason = relationship('PickupRescheduleReason')


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
    PickupRequestId = db.Column(ForeignKey('PickupRequests.PickupRequestId'), nullable=False)
    BookingId = db.Column(db.String(200, 'SQL_Latin1_General_CP1_CI_AS'))
    PickupAddressId = db.Column(ForeignKey('CustomerAddress.CustAddressId'), nullable=False)
    DeliveryAddressId = db.Column(ForeignKey('CustomerAddress.CustAddressId'), nullable=False)
    PickupDate = db.Column(db.DateTime, nullable=False)
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
    IsPaymentReady = db.Column(BIT, nullable=False, server_default=text("((0))"))
    IsCompleted = db.Column(BIT, nullable=False, server_default=text("((0))"))
    IsDeleted = db.Column(BIT, nullable=False, server_default=text("((0))"))
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordLastUpdatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordVersion = db.Column(Integer, nullable=False, server_default=text("((0))"))

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
    BasicAmount = db.Column(DECIMAL(18, 2), nullable=False)
    Discount = db.Column(DECIMAL(18, 2), nullable=False, server_default=text("((0.0))"))
    ServiceTaxAmount = db.Column(DECIMAL(18, 2))
    EstDeliveryDate = db.Column(db.DateTime)
    IsDeleted = db.Column(BIT, nullable=False, server_default=text("((0))"))
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordLastUpdatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordVersion = db.Column(Integer, nullable=False, server_default=text("((0))"))

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
    OrderReviewReasonId = db.Column(ForeignKey('OrderReviewReasons.OrderReviewReasonId'), nullable=False)
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
    BranchCode is a foreign key referencing BranchCode in Branches table.
    BranchCode2 is a foreign key referencing BranchCode in Branches table.
    BranchCode3 is a foreign key referencing BranchCode in Branches table.
    """
    __tablename__ = 'DeliveryUsers'

    DUserId = db.Column(Integer, primary_key=True)
    UserCode = db.Column(db.String(20, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    UserName = db.Column(db.String(500, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    MobileNo = db.Column(db.String(20, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    Password = db.Column(db.String(50, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    EmailId = db.Column(db.String(500, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    BranchCode = db.Column(ForeignKey('Branches.BranchCode'), nullable=False)
    BranchCode2 = db.Column(ForeignKey('Branches.BranchCode'))
    BranchCode3 = db.Column(ForeignKey('Branches.BranchCode'))
    Photo = db.Column(db.String(500, 'SQL_Latin1_General_CP1_CI_AS'))
    RegisteredDate = db.Column(db.DateTime, nullable=False)
    LastSiginTime = db.Column(db.DateTime, nullable=False)
    IsActive = db.Column(BIT, nullable=False, server_default=text("((1))"))
    IsDeleted = db.Column(BIT, nullable=False, server_default=text("((0))"))
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordLastUpdatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordVersion = db.Column(Integer, nullable=False, server_default=text("((0))"))

    Branch = relationship('Branch', primaryjoin='DeliveryUser.BranchCode == Branch.BranchCode')
    Branch1 = relationship('Branch', primaryjoin='DeliveryUser.BranchCode2 == Branch.BranchCode')
    Branch2 = relationship('Branch', primaryjoin='DeliveryUser.BranchCode3 == Branch.BranchCode')


class DeliveryUserLogin(db.Model):
    """
    This table contains the login information for delivery users.
    Relationship(s):
    DUserId is a foreign key referencing DUserId in DeliveryUsers table.
    """
    __tablename__ = 'DeliveryUserLogins'

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


class OTP(db.Model):
    """
    This table contains all the generated OTPs and corresponding mobile number and result from the SMS vendor.
    """
    __tablename__ = 'OTPs'

    OTPId = db.Column(Integer, primary_key=True)
    OTP = db.Column(Integer, nullable=False)
    MobileNumber = db.Column(db.String(20, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    Type = db.Column(db.String(50, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    Person = db.Column(db.String(100, 'SQL_Latin1_General_CP1_CI_AS'))
    Result = db.Column(db.String(500, 'SQL_Latin1_General_CP1_CI_AS'))


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
    """
    __tablename__ = 'DeliveryRequests'

    DeliveryRequestId = db.Column(Integer, primary_key=True)
    CustomerId = db.Column(ForeignKey('Customers.CustomerId'), nullable=False)
    DeliveryDate = db.Column(db.DateTime, nullable=False)
    DeliveryTimeSlotId = db.Column(ForeignKey('PickupTimeSlots.PickupTimeSlotId'))
    TimeSlotFrom = db.Column(Time)
    TimeSlotTo = db.Column(Time)
    BranchCode = db.Column(ForeignKey('Branches.BranchCode'), nullable=False)
    CustAddressId = db.Column(ForeignKey('CustomerAddress.CustAddressId'), nullable=False)
    BookingId = db.Column(db.String(200, 'SQL_Latin1_General_CP1_CI_AS'))
    OrderId = db.Column(ForeignKey('Orders.OrderId'), nullable=False)
    IsPartial = db.Column(BIT, nullable=False, server_default=text("((0))"))
    DUserId = db.Column(ForeignKey('DeliveryUsers.DUserId'))
    IsActive = db.Column(BIT, nullable=False, server_default=text("((1))"))
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordLastUpdatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordVersion = db.Column(Integer, nullable=False, server_default=text("((0))"))

    Branch = relationship('Branch')
    CustomerAddres = relationship('CustomerAddres')
    Customer = relationship('Customer')
    DeliveryUser = relationship('DeliveryUser')
    PickupTimeSlot = relationship('PickupTimeSlot')
    Order = relationship('Order')

    ReschuduleStatus = db.Column(Integer)
    ReschuduleDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    ReschuduleBy = db.Column(Integer)
    ReschuduleAddressId = db.Column(Integer)
    ReschuduleModifiedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    ReschuduleTimeSlotId = db.Column(Integer)
    ReschuduleTimeSlotFrom = db.Column(db.String(100, 'SQL_Latin1_General_CP1_CI_AS'))
    ReschuduleTimeSlotTo = db.Column(db.String(100, 'SQL_Latin1_General_CP1_CI_AS'))

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
    """
    __tablename__ = 'Deliveries'

    DeliveryId = db.Column(Integer, primary_key=True)
    EGRN = db.Column(db.String(50, 'SQL_Latin1_General_CP1_CI_AS'))
    CustomerId = db.Column(ForeignKey('Customers.CustomerId'), nullable=False)
    BranchCode = db.Column(ForeignKey('Branches.BranchCode'), nullable=False)
    DeliveryRequestId = db.Column(ForeignKey('DeliveryRequests.DeliveryRequestId'), nullable=False)
    BookingId = db.Column(db.String(200, 'SQL_Latin1_General_CP1_CI_AS'))
    PickupAddressId = db.Column(ForeignKey('CustomerAddress.CustAddressId'), nullable=False)
    DeliveryAddressId = db.Column(ForeignKey('CustomerAddress.CustAddressId'), nullable=False)
    DeliveryDate = db.Column(db.DateTime, nullable=False)
    DUserId = db.Column(ForeignKey('DeliveryUsers.DUserId'))
    Remarks = db.Column(db.String(500, 'SQL_Latin1_General_CP1_CI_AS'))
    IsActive = db.Column(BIT, nullable=False, server_default=text("((0))"))
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordLastUpdatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordVersion = db.Column(Integer, nullable=False, server_default=text("((0))"))

    Branch = relationship('Branch')
    Customer = relationship('Customer')
    DeliveryUser = relationship('DeliveryUser')
    CustomerAddres = relationship('CustomerAddres',
                                  primaryjoin='Delivery.DeliveryAddressId == CustomerAddres.CustAddressId')
    DeliveryRequest = relationship('DeliveryRequest')
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
    UserCode = db.Column(db.String(20, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    UserName = db.Column(db.String(500, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    MobileNo = db.Column(db.String(20, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    Password = db.Column(db.String(50, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    EmailId = db.Column(db.String(500, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    BranchCode = db.Column(ForeignKey('Branches.BranchCode'), nullable=False)
    BranchCode2 = db.Column(ForeignKey('Branches.BranchCode'))
    BranchCode3 = db.Column(ForeignKey('Branches.BranchCode'))
    Photo = db.Column(db.String(500, 'SQL_Latin1_General_CP1_CI_AS'))
    RegisteredDate = db.Column(db.DateTime, nullable=False)
    LastSiginTime = db.Column(db.DateTime, nullable=False)
    IsActive = db.Column(BIT, nullable=False, server_default=text("((1))"))
    IsDeleted = db.Column(BIT, nullable=False, server_default=text("((0))"))
    RecordCreatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordLastUpdatedDate = db.Column(db.DateTime, nullable=False, server_default=text("(getdate())"))
    RecordVersion = db.Column(Integer, nullable=False, server_default=text("((0))"))

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
    RecordCreatedDate = db.Column(db.DateTime, nullable=False)
    RecordVersion = db.Column(Integer, nullable=False)

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
