# ERP Paraguay V6 - Inventory Management Workflow

This document provides detailed flowcharts and documentation for the inventory management system in ERP Paraguay V6.

## Product Management Overview

```mermaid
flowchart TD
    Start([Inventory Management]) --> Menu{Action Type}

    Menu -->|Add Product| AddProduct
    Menu -->|Edit Product| EditProduct
    Menu -->|Delete Product| DeleteProduct
    Menu -->|Stock Adjustment| AdjustStock
    Menu -->|View Products| ViewProducts
    Menu -->|Low Stock Report| LowStock

    AddProduct --> AddEnd
    EditProduct --> EditEnd
    DeleteProduct --> DeleteEnd
    AdjustStock --> AdjustEnd
    ViewProducts --> ViewEnd
    LowStock --> ReportEnd
```

## Add New Product Flow

```mermaid
flowchart TD
    Start([Click "Add Product"]) --> ShowForm[Display Product Form]
    ShowForm --> EnterBasic[Enter Basic Information]

    EnterBasic --> EnterName[Enter Product Name]
    EnterName --> EnterBarcode[Enter/Generate Barcode]
    EnterBarcode --> EnterDesc[Enter Description]
    EnterDesc --> EnterPricing[Enter Pricing]

    EnterPricing --> EnterCost[Enter Cost Price]
    EnterCost --> EnterSale[Enter Sale Price]
    EnterSale --> ValidateMargin{Sale Price >=<br/>Cost Price?}
    ValidateMargin --> |No| ErrorMargin[Error: Sale price must be<br/>>= cost price]
    ValidateMargin --> |Yes| EnterStock

    ErrorMargin --> EnterSale

    EnterStock[Enter Initial Stock] --> ValidateStock{Stock >= 0?}
    ValidateStock --> |No| ErrorStock[Error: Stock cannot<br/>be negative]
    ValidateStock --> |Yes| SelectCategory

    ErrorStock --> EnterStock

    SelectCategory[Select Category] --> CheckCategory{Category Selected?}
    CheckCategory --> |No| CreateCategory[Create New Category]
    CheckCategory --> |Yes| SelectSupplier
    CreateCategory --> SelectSupplier

    SelectSupplier[Select Supplier] --> CheckSupplier{Supplier Selected?}
    CheckSupplier --> |No| CreateSupplier[Create New Supplier]
    CheckSupplier --> |Yes| ValidateForm

    CreateSupplier --> ValidateForm[Validate All Fields]

    ValidateForm --> ValidationCheck{All Valid?}
    ValidationCheck --> |No| ShowErrors[Display Validation Errors]
    ShowErrors --> ShowForm

    ValidationCheck --> |Yes| ConfirmSave{Confirm Save?}
    ConfirmSave --> |No| ShowForm
    ConfirmSave --> |Yes| CheckDuplicate[Check for Duplicate Barcode]

    CheckDuplicate --> DuplicateExists{Barcode<br/>Exists?}
    DuplicateExists --> |Yes| ErrorDuplicate[Error: Barcode already<br/>in use]
    DuplicateExists --> |No| BeginTxn[Begin Database Transaction]

    ErrorDuplicate --> EnterBarcode

    BeginTxn --> InsertProduct[INSERT INTO products]
    InsertProduct --> CommitTxn{Commit Successful?}

    CommitTxn --> |No| RollbackTxn[Rollback Transaction]
    RollbackTxn --> ErrorDB[Error: Failed to save product]
    ErrorDB --> ShowForm

    CommitTxn --> |Yes| InvalidateCache[Invalidate Product Cache]
    InvalidateCache --> LogAudit[Log Product Creation]
    LogAudit --> NotifySuccess[Display Success Message]
    NotifySuccess --> ClearForm[Clear Form]
    ClearForm --> OfferAnother{Add Another Product?}

    OfferAnother --> |Yes| ShowForm
    OfferAnother --> |No| End([Product Added])
```

## Edit Product Flow

```mermaid
flowchart TD
    Start([Select Product to Edit]) --> LoadProduct[Load Product from Database]
    LoadProduct --> DisplayForm[Display Form with Current Values]

    DisplayForm --> ModifyFields[User Modifies Fields]
    ModifyFields --> TrackChanges[Track Changed Fields]

    TrackChanges --> NoChanges{Any Changes?}
    NoChanges --> |No| InfoMsg[Info: No changes to save]
    InfoMsg --> End([No Changes Made])

    NoChanges --> |Yes| ValidateChanges[Validate Changed Fields]

    ValidateChanges --> PriceChanged{Price Changed?}
    PriceChanged --> |Yes| CheckNewMargin{New Sale >= Cost?}
    PriceChanged --> |No| CheckStock
    CheckNewMargin --> |No| ErrorMargin[Error: Sale price must be<br/>>= cost price]
    CheckNewMargin --> |Yes| CheckStock

    ErrorMargin --> DisplayForm

    CheckStock{Stock Changed?} --> |Yes| ValidateNewStock{New Stock >= 0?}
    CheckStock --> |No| ValidateOther
    ValidateNewStock --> |No| ErrorStock[Error: Stock cannot<br/>be negative]
    ValidateNewStock --> |Yes| ValidateOther

    ErrorStock --> DisplayForm

    ValidateOther[Validate Other Fields] --> AllValid{All Valid?}
    AllValid --> |No| ShowErrors[Display Validation Errors]
    ShowErrors --> DisplayForm

    AllValid --> |Yes| ConfirmUpdate{Confirm Update?}
    ConfirmUpdate --> |No| DisplayForm
    ConfirmUpdate --> |Yes| BeginTxn[Begin Database Transaction]

    BeginTxn --> UpdateProduct[UPDATE products SET ...]
    UpdateProduct --> CommitTxn{Commit Successful?}

    CommitTxn --> |No| RollbackTxn[Rollback Transaction]
    RollbackTxn --> ErrorDB[Error: Failed to update product]
    ErrorDB --> DisplayForm

    CommitTxn --> |Yes| InvalidateCache[Invalidate Product Cache]
    InvalidateCache --> LogAudit[Log Product Update]
    LogAudit --> NotifySuccess[Display Success Message]
    NotifySuccess --> End([Product Updated])
```

## Stock Adjustment Flow

```mermaid
flowchart TD
    Start([Request Stock Adjustment]) --> SelectProduct[Select Product]
    SelectProduct --> LoadProduct[Load Product with Current Stock]
    LoadProduct --> DisplayCurrent[Display: Name, Barcode,<br/>Current Stock, Location]

    DisplayCurrent --> SelectReason[Select Adjustment Reason]
    SelectReason --> ReasonType{Reason Type}

    ReasonType -->|Restock| Restock
    ReasonType -->|Damaged/Waste| Damaged
    ReasonType -->|Lost/Theft| Lost
    ReasonType -->|Physical Count| Physical
    ReasonType -->|Return| Return
    ReasonType -->|Other| Other

    Restock[Restock/Received] --> EnterQuantity
    Damaged[Damaged/Waste] --> EnterQuantity[Enter Quantity Change]
    Lost[Lost/Theft] --> EnterQuantity
    Physical[Physical Count Correction] --> EnterQuantity
    Return[Customer Return] --> EnterQuantity
    Other[Other - Enter Reason] --> EnterQuantity

    EnterQuantity --> ValidateQty{Quantity Valid?}
    ValidateQty --> |Zero| ErrorZero[Error: Quantity cannot be zero]
    ValidateQty --> |Negative| AllowNegative{Allow Negative?}
    ValidateQty --> |Positive| CalculateNewStock

    ErrorZero --> EnterQuantity

    AllowNegative --> |Restock| ErrorNegativeRestock[Error: Restock must be positive]
    AllowNegative -->|Others| CalculateNewStock[Calculate New Stock Level]
    ErrorNegativeRestock --> EnterQuantity

    CalculateNewStock --> CheckNegative{New Stock < 0?}
    CheckNegative --> |Yes| ErrorNegative[Error: Cannot have negative stock]
    CheckNegative --> |No| ConfirmAdjustment

    ErrorNegative --> EnterQuantity

    ConfirmAdjustment{Confirm Adjustment?} --> |No| SelectReason
    ConfirmAdjustment --> |Yes| ShowSummary[Display Adjustment Summary]

    ShowSummary --> BeginTxn[Begin Database Transaction]

    BeginTxn --> CreateAdjustment[CREATE stock_adjustment Record]
    CreateAdjustment --> UpdateStock[UPDATE products SET stock = ?]
    UpdateStock --> CommitTxn{Commit Successful?}

    CommitTxn --> |No| RollbackTxn[Rollback Transaction]
    RollbackTxn --> ErrorDB[Error: Adjustment failed]
    ErrorDB --> ShowSummary

    CommitTxn --> |Yes| InvalidateCache[Invalidate Product Cache]
    InvalidateCache --> LogAudit[Log Stock Adjustment]
    LogAudit --> PrintReport{Print Adjustment Report?}

    PrintReport --> |Yes| GenerateReport[Generate and Print Report]
    PrintReport --> |No| NotifySuccess
    GenerateReport --> NotifySuccess[Display Success Message]
    NotifySuccess --> DisplayNewStock[Display New Stock Level]
    DisplayNewStock --> CheckLowStock{New Stock <=<br/>Low Threshold?}

    CheckLowStock --> |Yes| WarnLowStock[Warning: Low Stock Alert]
    CheckLowStock --> |No| End
    WarnLowStock --> End([Adjustment Complete])
```

## Low Stock Alert Flow

```mermaid
flowchart TD
    Start([System Check or User Request]) --> QueryProducts[Query All Active Products]
    QueryProducts --> CheckThreshold[Check Each Product:<br/>stock <= LOW_STOCK_THRESHOLD]

    CheckThreshold --> IterateProducts[Loop Through Products]
    IterateProducts --> ProductCheck{Stock <=<br/>Threshold?}

    ProductCheck --> |Yes| AddToList[Add to Low Stock List]
    ProductCheck --> |No| NextProduct

    AddToList --> NextProduct{More Products?}
    NextProduct --> |Yes| IterateProducts
    NextProduct --> |No| CheckListSize

    NextProduct --> IterateProducts

    CheckListSize{Items in List?} --> |Zero| NoAlert[No Low Stock Items]
    CheckListSize -->|Has Items| SortList

    NoAlert --> End([Check Complete])

    SortList[Sort by Stock Ascending] --> GenerateReport[Generate Low Stock Report]
    GenerateReport --> DisplayReport[Display Report to User]

    DisplayReport --> UserAction{User Action}

    UserAction -->|Create Order| CreateOrder[Create Purchase Order]
    UserAction -->|Print Report| PrintReport[Print Low Stock Report]
    UserAction -->|Export| ExportCSV[Export to CSV]
    UserAction -->|Close| End

    CreateOrder --> OrderForm[Open Purchase Order Form]
    PrintReport --> End
    ExportCSV --> End
    OrderForm --> End
```

## Product Deletion Flow

```mermaid
flowchart TD
    Start([Select Product to Delete]) --> LoadProduct[Load Product]
    LoadProduct --> CheckUsage[Check Product Usage]

    CheckUsage --> InSales{Product in<br/>Sales?}
    InSales --> |Yes| ShowHistory[Product has sales history]
    ShowHistory --> OfferDeactivate[Offer Deactivation Instead]
    OfferDeactivate --> UserChoice{User Choice}

    UserChoice -->|Deactivate| DeactivateProduct
    UserChoice -->|Cancel| End([Cancelled])

    InSales --> |No| ConfirmDelete{Confirm Permanent<br/>Deletion?}

    ConfirmDelete --> |No| End
    ConfirmDelete --> |Yes| BeginTxn[Begin Database Transaction]

    BeginTxn --> DeleteProduct[DELETE FROM products]
    DeleteProduct --> CommitTxn{Commit Successful?}

    CommitTxn --> |No| RollbackTxn[Rollback Transaction]
    RollbackTxn --> ErrorDB[Error: Deletion failed]
    ErrorDB --> End

    CommitTxn --> |Yes| InvalidateCache[Invalidate Product Cache]
    InvalidateCache --> LogAudit[Log Product Deletion]
    LogAudit --> NotifySuccess[Display Success Message]
    NotifySuccess --> End([Product Deleted])

    DeactivateProduct[Set is_active = false] --> BeginDeactivate[Begin Transaction]
    BeginDeactivate --> UpdateActive[UPDATE products<br/>SET is_active = false]
    UpdateActive --> CommitDeactivate{Commit Successful?}

    CommitDeactivate --> |No| RollbackDeactivate[Rollback]
    RollbackDeactivate --> ErrorDeactivate[Error: Deactivation failed]
    ErrorDeactivate --> End

    CommitDeactivate --> |Yes| InvalidateCache
    InvalidateCache --> LogDeactivate[Log Deactivation]
    LogDeactivate --> NotifyDeactivate[Display: Product Deactivated]
    NotifyDeactivate --> End([Product Deactivated])
```

## Category Management Flow

```mermaid
flowchart TD
    Start([Category Management]) --> Action{Action Type}

    Action -->|View Categories| ViewCategories[List All Categories]
    Action -->|Add Category| AddCategory
    Action -->|Edit Category| EditCategory
    Action -->|Delete Category| DeleteCategory

    ViewCategories --> DisplayCategories[Display Categories with<br/>Product Count]
    DisplayCategories --> ViewEnd([View Complete])

    AddCategory --> ShowAddForm[Display Category Form]
    ShowAddForm --> EnterName[Enter Category Name]
    EnterName --> EnterDesc[Enter Description (Optional)]
    EnterDesc --> ValidateCategory[Validate Category]
    ValidateCategory --> CategoryValid{Valid?}
    CategoryValid --> |No| ShowCategoryError[Display Error]
    ShowCategoryError --> ShowAddForm
    CategoryValid --> |Yes| CheckDuplicateCategory{Duplicate Name?}
    CheckDuplicateCategory --> |Yes| ErrorDuplicate[Error: Category name exists]
    ErrorDuplicate --> ShowAddForm
    CheckDuplicateCategory --> |No| SaveCategory[Save Category to DB]
    SaveCategory --> CategorySuccess([Category Created])

    EditCategory --> SelectCategory[Select Category to Edit]
    SelectCategory --> LoadCategory[Load Category Data]
    LoadCategory --> ShowEditForm[Display Edit Form]
    ShowEditForm --> ModifyCategory[User Modifies Fields]
    ModifyCategory --> ValidateEdit[Validate Changes]
    ValidateEdit --> EditValid{Valid?}
    EditValid --> |No| ShowEditError[Display Error]
    ShowEditError --> ShowEditForm
    EditValid --> |Yes| UpdateCategory[Update Category in DB]
    UpdateCategory --> EditSuccess([Category Updated])

    DeleteCategory --> SelectDeleteCategory[Select Category]
    SelectDeleteCategory --> CheckProducts{Has Products?}
    CheckProducts --> |Yes| ShowProductError[Error: Category has products]
    ShowProductError --> OfferReassign[Offer to Reassign Products]
    OfferReassign --> ReassignProducts[Reassign Products to Other Category]
    ReassignProducts --> CheckProducts
    CheckProducts --> |No| ConfirmDeleteCategory{Confirm Deletion?}
    ConfirmDeleteCategory --> |No| DeleteEnd([Cancelled])
    ConfirmDeleteCategory --> |Yes| DeleteCategoryRecord[Delete Category from DB]
    DeleteCategoryRecord --> DeleteSuccess([Category Deleted])
```

## Supplier Management Flow

```mermaid
flowchart TD
    Start([Supplier Management]) --> Action{Action Type}

    Action -->|View Suppliers| ViewSuppliers[List All Suppliers]
    Action -->|Add Supplier| AddSupplier
    Action -->|Edit Supplier| EditSupplier
    Action -->|Delete Supplier| DeleteSupplier

    ViewSuppliers --> DisplaySuppliers[Display Suppliers with<br/>Product Count]
    DisplaySuppliers --> ViewEnd([View Complete])

    AddSupplier --> ShowAddForm[Display Supplier Form]
    ShowAddForm --> EnterName[Enter Supplier Name]
    EnterName --> EnterContact[Enter Email, Phone, Address]
    EnterContact --> EnterTaxID[Enter Tax ID (Optional)]
    EnterTaxID --> ValidateSupplier[Validate Supplier]
    ValidateSupplier --> SupplierValid{Valid?}
    SupplierValid --> |No| ShowSupplierError[Display Error]
    ShowSupplierError --> ShowAddForm
    SupplierValid --> |Yes| CheckDuplicateSupplier{Duplicate Email/Tax ID?}
    CheckDuplicateSupplier --> |Yes| ErrorDuplicate[Error: Supplier exists]
    ErrorDuplicate --> ShowAddForm
    CheckDuplicateSupplier --> |No| SaveSupplier[Save Supplier to DB]
    SaveSupplier --> SupplierSuccess([Supplier Created])

    EditSupplier --> SelectSupplier[Select Supplier to Edit]
    SelectSupplier --> LoadSupplier[Load Supplier Data]
    LoadSupplier --> ShowEditForm[Display Edit Form]
    ShowEditForm --> ModifySupplier[User Modifies Fields]
    ModifySupplier --> ValidateEdit[Validate Changes]
    ValidateEdit --> EditValid{Valid?}
    EditValid --> |No| ShowEditError[Display Error]
    ShowEditError --> ShowEditForm
    EditValid --> |Yes| UpdateSupplier[Update Supplier in DB]
    UpdateSupplier --> EditSuccess([Supplier Updated])

    DeleteSupplier --> SelectDeleteSupplier[Select Supplier]
    SelectDeleteSupplier --> CheckProducts{Has Products?}
    CheckProducts --> |Yes| ShowProductError[Error: Supplier has products]
    ShowProductError --> OfferReassign[Offer to Reassign Products]
    OfferReassign --> ReassignProducts[Reassign Products]
    ReassignProducts --> CheckProducts
    CheckProducts --> |No| ConfirmDeleteSupplier{Confirm Deletion?}
    ConfirmDeleteSupplier --> |No| DeleteEnd([Cancelled])
    ConfirmDeleteSupplier --> |Yes| DeleteSupplierRecord[Delete Supplier from DB]
    DeleteSupplierRecord --> DeleteSuccess([Supplier Deleted])
```

## Inventory Report Generation

```mermaid
flowchart TD
    Start([Request Inventory Report]) --> SelectReport{Report Type}

    SelectReport -->|Stock Status| StockStatus[Stock Status Report]
    SelectReport -->|Low Stock| LowStock[Low Stock Report]
    SelectReport -->|Movement| Movement[Stock Movement Report]
    SelectReport -->|Valuation| Valuation[Inventory Valuation]

    StockStatus --> CheckCache1{Cache Available?}
    LowStock --> CheckCache2{Cache Available?}
    Movement --> CheckCache3{Cache Available?}
    Valuation --> CheckCache4{Cache Available?}

    CheckCache1 --> |Yes| GetCached1
    CheckCache1 --> |No| QueryWithEager1
    CheckCache2 --> |Yes| GetCached2
    CheckCache2 --> |No| QueryWithEager2
    CheckCache3 --> |Yes| GetCached3
    CheckCache3 --> |No| QueryWithEager3
    CheckCache4 --> |Yes| GetCached4
    CheckCache4 --> |No| QueryWithEager4

    GetCached1[Get from Cache] --> Display1
    GetCached2[Get from Cache] --> Display2
    GetCached3[Get from Cache] --> Display3
    GetCached4[Get from Cache] --> Display4

    QueryWithEager1[Use Eager Loading] --> CalculateStatus
    QueryWithEager2[Use Eager Loading] --> CalculateLow
    QueryWithEager3[Use Eager Loading] --> CalculateMovement
    QueryWithEager4[Use Eager Loading] --> CalculateValuation

    CalculateStatus[Calculate Stock Status<br/>and Reorder Points] --> CacheResult1
    CalculateLow[Identify Low Stock<br/>Items] --> CacheResult2
    CalculateMovement[Analyze Stock<br/>Adjustments] --> CacheResult3
    CalculateValuation[Calculate Total<br/>Inventory Value] --> CacheResult4

    CacheResult1[Cache Result] --> Display1[Display Report]
    CacheResult2[Cache Result] --> Display2[Display Report]
    CacheResult3[Cache Result] --> Display3[Display Report]
    CacheResult4[Cache Result] --> Display4[Display Report]

    Display1 --> ExportOptions
    Display2 --> ExportOptions
    Display3 --> ExportOptions
    Display4 --> ExportOptions

    ExportOptions{Export Options} -->|Print| Print[Print Report]
    ExportOptions -->|PDF| GeneratePDF[Generate PDF]
    ExportOptions -->|Excel| ExportExcel[Export to Excel]
    ExportOptions -->|View| End([Display Complete])

    Print --> End
    GeneratePDF --> End
    ExportExcel --> End
```

## Batch Import Flow

```mermaid
flowchart TD
    Start([Select Import Option]) --> SelectFile[Select CSV/Excel File]
    SelectFile --> ValidateFile{File Valid?}
    ValidateFile --> |No| ErrorFile[Error: Invalid file format]
    ErrorFile --> End

    ValidateFile --> |Yes| ParseFile[Parse File]
    ParseFile --> ValidateHeaders{Headers Valid?}
    ValidateHeaders --> |No| ErrorHeaders[Error: Missing required columns]
    ErrorHeaders --> End

    ValidateHeaders --> |Yes| ReadRows[Read Data Rows]
    ReadRows --> ValidateData[Validate Each Row]

    ValidateData --> RowValid{Data Valid?}
    RowValid --> |No| CollectErrors[Collect Validation Errors]
    RowValid --> |Yes| CheckDuplicateRow{Duplicate Barcode?}

    CollectErrors --> MoreRows{More Rows?}
    CheckDuplicateRow --> |Yes| ErrorDuplicate[Error: Duplicate barcode]
    ErrorDuplicate --> MarkFailed[Mark Row as Failed]
    CheckDuplicateRow --> |No| AddToImport[Add to Import List]

    MarkFailed --> MoreRows
    AddToImport --> MoreRows{More Rows?}

    MoreRows --> |Yes| ReadRows
    MoreRows --> |No| ShowSummary[Display Import Summary]

    ShowSummary --> HasFailures{Any Failures?}
    HasFailures --> |Yes| DisplayErrors[Display Errors]
    HasFailures --> |No| ConfirmImport

    DisplayErrors --> UserChoice{User Choice}
    UserChoice -->|Cancel| End([Import Cancelled])
    UserChoice -->|Import Anyway| ConfirmImport
    UserChoice -->|Fix and Retry| End

    ConfirmImport[Confirm Import] --> BeginTxn[Begin Database Transaction]

    BeginTxn --> ImportLoop[Loop Through Import List]
    ImportLoop --> InsertProduct[INSERT INTO products]
    InsertProduct --> MoreImports{More Products?}
    MoreImports --> |Yes| ImportLoop
    MoreImports --> |No| CommitTxn

    CommitTxn{Commit Successful?} --> |No| RollbackTxn[Rollback Transaction]
    RollbackTxn --> ErrorDB[Error: Import failed]
    ErrorDB --> End

    CommitTxn --> |Yes| InvalidateCache[Invalidate Product Cache]
    InvalidateCache --> LogImport[Log Import in Audit]
    LogImport --> DisplaySuccess[Display Import Results]
    DisplaySuccess --> End([Import Complete])
```

## Inventory Business Rules

### Product Validation

1. **Required Fields**
   - Name: Required, max 100 characters
   - Cost Price: Required, must be positive
   - Sale Price: Required, must be >= cost price
   - Stock: Required, must be >= 0
   - Category: Required

2. **Optional Fields**
   - Barcode: Optional, must be unique if provided
   - Description: Optional, free text
   - Supplier: Optional

3. **Business Rules**
   - Sale price must be >= cost price (enforced)
   - Stock cannot be negative (enforced)
   - Barcodes must be unique (enforced)
   - Product names are case-insensitive unique (recommended)

### Stock Management

1. **Stock Deduction**
   - Occurs when sale is completed
   - Quantity deducted per sale item
   - Validation prevents insufficient stock
   - Transactional: all or nothing

2. **Stock Restoration**
   - Occurs when sale is cancelled
   - Full quantity restored per sale item
   - Automatic with sale cancellation

3. **Stock Adjustments**
   - Can increase or decrease stock
   - Requires reason code
   - Creates audit trail
   - Cannot result in negative stock

4. **Low Stock Threshold**
   - Default: 10 units
   - Configurable via LOW_STOCK_THRESHOLD
   - Triggers alerts and reports
   - Checked on stock changes

### Category Management

1. **Category Rules**
   - Name must be unique
   - Can be deactivated (not deleted if has products)
   - Products can be reassigned
   - Optional description field

2. **Category Deletion**
   - Only allowed if no products assigned
   - Or products must be reassigned first
   - Deactivation preferred over deletion

### Supplier Management

1. **Supplier Rules**
   - Email must be unique (if provided)
   - Tax ID must be unique (if provided)
   - Can be deactivated (not deleted if has products)
   - Products can be reassigned

2. **Supplier Deletion**
   - Only allowed if no products assigned
   - Or products must be reassigned first
   - Deactivation preferred over deletion

---

**Document Version:** 1.0
**Last Updated:** 2025-03-14
