# ERP Paraguay V6 - Sales Workflow

This document provides detailed flowcharts and documentation for the sales management workflow in ERP Paraguay V6.

## Complete Sales Process Flow

```mermaid
flowchart TD
    Start([Start: User clicks New Sale]) --> SelectCustomer[Select Customer]
    SelectCustomer --> |New Customer| CreateCustomer[Create Customer Record]
    CreateCustomer --> SelectCustomer
    SelectCustomer --> |Existing Customer| ValidateCustomer{Customer Valid?}
    ValidateCustomer --> |No| Error1[Show Error: Invalid Customer]
    ValidateCustomer --> |Yes| AddItems[Add Products to Sale]

    AddItems --> ScanBarcode[Scan/Select Product]
    ScanBarcode --> GetProduct[Retrieve Product from DB]
    GetProduct --> CheckStock{Stock Available?}
    CheckStock --> |No| Error2[Show Error: Insufficient Stock]
    CheckStock --> |Yes| SetQuantity[Set Quantity]
    SetQuantity --> SetPrice{Override Price?}
    SetPrice --> |Yes| EnterPrice[Enter Custom Price]
    SetPrice --> |No| UsePrice[Use Sale Price from DB]
    EnterPrice --> AddDiscount{Apply Discount?}
    UsePrice --> AddDiscount
    AddDiscount --> |Yes| EnterDiscount[Enter Discount Amount]
    AddDiscount --> |No| CalculateLine[Calculate Line Subtotal]
    EnterDiscount --> CalculateLine
    CalculateLine --> AddToSale[Add to Sale Items List]
    AddToSale --> MoreItems{More Items?}
    MoreItems --> |Yes| ScanBarcode
    MoreItems --> |No| ReviewSale[Review Sale Summary]

    Error1 --> SelectCustomer
    Error2 --> AddItems

    ReviewSale --> ConfirmSale{Confirm Sale?}
    ConfirmSale --> |No| EditSale[Edit Sale Items]
    EditSale --> AddItems
    ConfirmSale --> |Yes| SelectPayment[Select Payment Method]

    SelectPayment --> PaymentMethod{Payment Method}
    PaymentMethod -->|Cash| ProcessCash[Process Cash Payment]
    PaymentMethod -->|Credit| ValidateCredit{Customer Credit OK?}
    PaymentMethod -->|Debit| ProcessDebit[Process Debit Card]
    PaymentMethod -->|Transfer| ProcessTransfer[Process Bank Transfer]

    ValidateCredit --> |No| Error3[Show Error: Credit Limit Exceeded]
    ValidateCredit --> |Yes| CreateCreditSale[Create Credit Sale]

    ProcessCash --> BeginTxn[Begin Database Transaction]
    ProcessDebit --> BeginTxn
    ProcessTransfer --> BeginTxn
    CreateCreditSale --> BeginTxn

    BeginTxn --> CreateSaleRecord[Create Sale Record]
    CreateSaleRecord --> CreateSaleItems[Create Sale Item Records]
    CreateSaleItems --> UpdateStock[Update Product Stock]
    UpdateStock --> CreatePayment[Create Payment Record]
    CreatePayment --> CommitTxn{Commit Transaction?}

    CommitTxn --> |Success| InvalidateCache[Invalidate Product Cache]
    CommitTxn --> |Failure| RollbackTxn[Rollback Transaction]
    RollbackTxn --> Error4[Show Error: Sale Failed]

    InvalidateCache --> GenerateInvoice[Generate Invoice/PDF]
    GenerateInvoice --> PrintReceipt{Print Receipt?}
    PrintReceipt --> |Yes| Print[Print Receipt]
    PrintReceipt --> |No| DisplaySuccess[Display Success Message]
    Print --> DisplaySuccess

    Error3 --> SelectPayment
    Error4 --> SelectPayment

    DisplaySuccess --> End([End: Sale Complete])
```

## Cash Sale Detailed Flow

```mermaid
sequenceDiagram
    actor User
    participant UI as Sales Window
    participant Service as Sales Service
    participant ProductSvc as Product Service
    participant CustomerSvc as Customer Service
    participant DB as Database
    participant Cache as Cache
    participant PDF as PDF Generator

    User->>UI: Start new sale
    UI->>UI: Clear sale form

    Note over User,UI: Step 1: Select Customer
    User->>UI: Select customer from list
    UI->>CustomerSvc: get_customer_by_id(id)
    CustomerSvc->>Cache: Check cache
    alt Cache Miss
        CustomerSvc->>DB: SELECT * FROM customers WHERE id = ?
        DB-->>CustomerSvc: Customer data
        CustomerSvc->>Cache: Cache customer (10 min TTL)
    end
    Cache-->>CustomerSvc: Customer data
    CustomerSvc-->>UI: Customer object
    UI->>UI: Display customer info

    Note over User,Service: Step 2: Add Products
    loop For each product
        User->>UI: Scan barcode or select product
        UI->>ProductSvc: get_product_by_id(id)
        ProductSvc->>Cache: Check cache
        alt Cache Miss
            ProductSvc->>DB: SELECT * FROM products WHERE id = ?
            DB-->>ProductSvc: Product data
            ProductSvc->>Cache: Cache product (5 min TTL)
        end
        Cache-->>ProductSvc: Product data
        ProductSvc-->>UI: Product object

        UI->>UI: Display product and price
        User->>UI: Enter quantity
        UI->>UI: Validate quantity <= stock
        User->>UI: Optionally apply discount
        UI->>UI: Calculate line subtotal
        UI->>UI: Add to sale items grid
    end

    Note over User,Service: Step 3: Review and Confirm
    UI->>UI: Calculate sale totals
    UI->>UI: Display subtotal, tax, total
    User->>UI: Confirm sale
    UI->>UI: Validate sale has items

    Note over User,DB: Step 4: Process Sale
    UI->>Service: create_sale(customer_id, items, payment_method='cash')
    Service->>Service: Validate customer exists
    Service->>Service: Validate all products exist
    Service->>Service: Calculate totals with tax

    Service->>DB: BEGIN TRANSACTION
    Service->>DB: INSERT INTO sales (...)
    DB-->>Service: sale_id

    loop For each sale item
        Service->>DB: INSERT INTO sale_items (...)
    end

    loop For each product
        Service->>DB: UPDATE products SET stock = stock - ? WHERE id = ?
    end

    Service->>DB: INSERT INTO payments (amount, payment_method, ...)
    Service->>DB: COMMIT
    DB-->>Service: Transaction committed

    Service->>Cache: Invalidate product cache
    Service->>Cache: Invalidate customer cache
    Service-->>UI: (success, None, sale_id)

    Note over User,PDF: Step 5: Generate Invoice
    UI->>PDF: generate_invoice_pdf(sale_id)
    PDF->>DB: Query sale with all details
    PDF->>PDF: Format with company info
    PDF->>PDF: Add line items and totals
    PDF-->>UI: PDF document

    UI->>User: Display confirmation
    UI->>User: Show/print invoice
    UI->>UI: Clear form for next sale
```

## Credit Sale with Payment Flow

```mermaid
flowchart TD
    Start([Credit Sale Created]) --> CheckBalance{Customer Balance OK?}
    CheckBalance --> |Yes| CreateSale[Create Sale with Status='completed']
    CheckBalance --> |No| Error1[Error: Balance Exceeds Limit]

    CreateSale --> UpdateBalance[Update Customer Balance]
    UpdateBalance --> AddTotalToBalance[Add Sale Total to Balance]
    AddTotalToBalance --> CreateSaleRecord[Create Sale Record]
    CreateSaleRecord --> NoPayment[No Payment Created Initially]

    NoPayment --> DisplayBalance[Display Updated Balance to User]
    DisplayBalance --> OfferPayment{Customer Wants to Pay Now?}

    OfferPayment --> |Yes| EnterPayment[Enter Payment Amount]
    OfferPayment --> |No| End([Sale Complete - Credit])

    EnterPayment --> ValidateAmount{Amount Valid?}
    ValidateAmount --> |Exceeds Balance| Error2[Error: Payment Exceeds Balance]
    ValidateAmount --> |Zero or Negative| Error3[Error: Invalid Amount]
    ValidateAmount --> |OK| CheckRemaining{Payment Covers Balance?}

    CheckRemaining --> |Full Payment| ProcessFull[Process Full Payment]
    CheckRemaining --> |Partial Payment| ProcessPartial[Process Partial Payment]

    ProcessFull --> UpdateStatus[Set Sale Status to 'paid']
    ProcessFull --> ZeroBalance[Set Customer Balance to 0]
    ProcessFull --> CreatePayment[Create Payment Record]

    ProcessPartial --> ReduceBalance[Reduce Customer Balance]
    ProcessPartial --> KeepStatus[Keep Sale Status as 'completed']
    ProcessPartial --> CreatePayment

    CreatePayment --> SavePayment[Save Payment to Database]
    SavePayment --> InvalidateCache[Invalidate Customer Cache]
    InvalidateCache --> DisplayNewBalance[Display New Balance]
    DisplayNewBalance --> MorePayments{More Payments?}
    MorePayments --> |Yes| EnterPayment
    MorePayments --> |No| End

    Error1 --> End
    Error2 --> EnterPayment
    Error3 --> EnterPayment
```

## Sale Cancellation Flow

```mermaid
flowchart TD
    Start([Request Cancel Sale]) --> VerifyAuth{User Authorized?}
    VerifyAuth --> |No| ErrorAuth[Error: Unauthorized]
    VerifyAuth --> |Yes| GetSale[Retrieve Sale Record]

    GetSale --> CheckStatus{Sale Status?}
    CheckStatus --> |Already Cancelled| ErrorCancelled[Error: Already Cancelled]
    CheckStatus --> |Completed| ProceedCancel[Proceed with Cancellation]
    CheckStatus --> |Other| ErrorStatus[Error: Cannot Cancel]

    ProceedCancel --> GetSaleItems[Get All Sale Items]
    GetSaleItems --> BeginTxn[Begin Database Transaction]

    BeginTxn --> RestoreStock[Restore Product Stock]
    RestoreStock --> LoopItems[Loop Through Sale Items]
    LoopItems --> GetProduct[Get Product Record]
    GetProduct --> UpdateStock[UPDATE products<br/>SET stock = stock + quantity]
    UpdateStock --> MoreItems{More Items?}
    MoreItems --> |Yes| GetProduct
    MoreItems --> |No| UpdateStatus

    UpdateStatus[Update Sale Status to 'cancelled'] --> CheckPayment{Payment Exists?}
    CheckPayment --> |Yes| ReversePayment[Reverse Payment if Needed]
    CheckPayment --> |No| CheckCredit
    ReversePayment --> CheckCredit{Was Credit Sale?}
    CheckCredit --> |Yes| ReverseBalance[Reverse Customer Balance]
    CheckCredit --> |No| CommitTxn
    ReverseBalance --> CommitTxn[Commit Transaction]

    CommitTxn --> Success{Commit Successful?}
    Success --> |Yes| InvalidateCache[Invalidate Caches]
    Success --> |No| RollbackTxn[Rollback Transaction]

    InvalidateCache --> LogAudit[Log Cancellation in Audit]
    LogAudit --> NotifyUser[Notify User of Success]
    NotifyUser --> End([Cancellation Complete])

    RollbackTxn --> ErrorRollback[Error: Cancellation Failed]
    ErrorRollback --> End

    ErrorAuth --> End
    ErrorCancelled --> End
    ErrorStatus --> End
```

## Multiple Installments Flow

```mermaid
sequenceDiagram
    actor User
    participant UI as Sales Window
    participant Service as Sales Service
    participant CustSvc as Customer Service
    participant DB as Database
    participant Cache as Cache

    Note over User,DB: Scenario: Customer bought on credit,<br/>now making installment payments

    User->>UI: Open Payments Window
    UI->>Service: get_sale_by_id(sale_id)
    Service->>DB: Query sale with items and payments
    DB-->>Service: Sale data
    Service-->>UI: Sale with balance_due

    UI->>UI: Display sale details
    UI->>UI: Show payment history
    UI->>UI: Display remaining balance

    User->>UI: Enter payment amount
    UI->>Service: validate_payment_amount(sale_id, amount)

    Service->>Service: Calculate total_paid from payments
    Service->>Service: Calculate remaining = total - total_paid
    Service->>Service: Validate amount <= remaining

    alt Amount exceeds remaining
        Service-->>UI: Error: Payment exceeds balance
        UI->>User: Show error message
    else Amount valid
        Service->>DB: BEGIN TRANSACTION
        Service->>DB: INSERT INTO payments (sale_id, amount, payment_method, ...)
        Service->>CustSvc: update_customer_balance(customer_id, -amount)
        CustSvc->>DB: UPDATE customers SET balance = balance - ? WHERE id = ?
        Service->>DB: COMMIT

        alt All payments made
            Service->>DB: UPDATE sales SET status = 'paid' WHERE id = ?
        end

        Service->>Cache: Invalidate customer cache
        Service-->>UI: Payment recorded successfully

        UI->>UI: Refresh payment list
        UI->>UI: Update balance display
        UI->>User: Show success confirmation

        alt Balance fully paid
            UI->>UI: Display "Sale fully paid" message
        else Balance remaining
            UI->>UI: Display new balance
        end
    end
```

## Stock Adjustment Workflow

```mermaid
flowchart TD
    Start([Stock Discrepancy Found]) --> SelectProduct[Select Product]
    SelectProduct --> ViewCurrent[View Current Stock]
    ViewCurrent --> EnterReason[Select Adjustment Reason]

    EnterReason --> ReasonType{Reason Type}
    ReasonType -->|Damaged| Damaged[Damaged/Waste]
    ReasonType -->|Restock| Restock[Restock/Received]
    ReasonType -->|Lost| Lost[Lost/Theft]
    ReasonType -->|Count| Physical[Physical Count]
    ReasonType -->|Other| OtherOther[Other Reason]

    Damaged --> EnterQuantity
    Restock --> EnterQuantity[Enter Quantity Change]
    Lost --> EnterQuantity
    Physical --> EnterQuantity
    OtherOther --> EnterQuantity

    EnterQuantity --> ValidateQty{Quantity Valid?}
    ValidateQty --> |No| Error1[Error: Invalid Quantity]
    ValidateQty --> |Yes| CalculateNew[Calculate New Stock]

    CalculateNew --> CheckNegative{New Stock < 0?}
    CheckNegative --> |Yes| Error2[Error: Cannot Have Negative Stock]
    CheckNegative --> |No| ConfirmAdjustment{Confirm Adjustment?}

    ConfirmAdjustment --> |No| SelectProduct
    ConfirmAdjustment --> |Yes| BeginTxn[Begin Database Transaction]

    BeginTxn --> CreateRecord[CREATE stock_adjustment Record]
    CreateRecord --> UpdateProductStock[UPDATE products.stock]
    UpdateProductStock --> CommitTxn{Commit Transaction?}

    CommitTxn --> |Success| InvalidateCache[Invalidate Product Cache]
    CommitTxn --> |Failure| RollbackTxn[Rollback Transaction]

    InvalidateCache --> LogAudit[Log in Audit Trail]
    LogAudit --> DisplayNew[Display New Stock Level]
    DisplayNew --> PrintReport{Print Adjustment Report?}
    PrintReport --> |Yes| Print[Print Adjustment Report]
    PrintReport --> |No| End([Adjustment Complete])
    Print --> End

    Error1 --> EnterQuantity
    Error2 --> EnterQuantity
    RollbackTxn --> Error3[Error: Adjustment Failed]
    Error3 --> End
```

## Sales Report Generation Flow

```mermaid
flowchart TD
    Start([Request Sales Report]) --> SelectPeriod[Select Date Period]
    SelectPeriod --> ValidateDates{Dates Valid?}
    ValidateDates --> |No| Error1[Error: Invalid Date Range]
    ValidateDates --> |Yes| SelectReportType{Report Type}

    SelectReportType -->|Summary| SummaryReport[Sales Summary Report]
    SelectReportType -->|Detail| DetailReport[Sales Detail Report]
    SelectReportType -->|Profit| ProfitReport[Profit Margin Report]
    SelectReportType -->|Top Products| TopProducts[Top Products Report]
    SelectReportType -->|Top Customers| TopCustomers[Top Customers Report]

    Error1 --> SelectPeriod

    SummaryReport --> CheckCache{Cache Available?}
    DetailReport --> CheckCache
    ProfitReport --> CheckCache
    TopProducts --> CheckCache
    TopCustomers --> CheckCache

    CheckCache --> |Yes| GetFromCache[Get Report from Cache]
    CheckCache --> |No| QueryDatabase[Query Database with Eager Loading]

    QueryDatabase --> UseEagerLoad[Use joinedload/selectinload]
    UseEagerLoad --> FetchSales[Fetch Sales with Items]
    FetchSales --> FetchProducts[Fetch Product Details]
    FetchProducts --> FetchCustomers[Fetch Customer Details]
    FetchCustomers --> CalculateMetrics[Calculate Metrics]

    CalculateMetrics --> ProcessSummary{Report Type?}
    ProcessSummary -->|Summary| CalcSummary[Calculate: Total Sales, Count, Average]
    ProcessSummary -->|Detail| CalcDetail[Group by Date, Payment Method]
    ProcessSummary -->|Profit| CalcProfit[Calculate: Cost, Revenue, Margin]
    ProcessSummary -->|Top Products| CalcTopProd[Rank Products by Quantity/Revenue]
    ProcessSummary -->|Top Customers| CalcTopCust[Rank Customers by Purchase]

    CalcSummary --> FormatReport
    CalcDetail --> FormatReport[Format Report Data]
    CalcProfit --> FormatReport
    CalcTopProd --> FormatReport
    CalcTopCust --> FormatReport

    FormatReport --> CacheResult[Cache Report Result with TTL]
    GetFromCache --> DisplayData

    CacheResult --> DisplayData[Display Report in Grid]
    DisplayData --> ExportOptions{Export Options}

    ExportOptions -->|Print| PrintReport[Send to Printer]
    ExportOptions -->|PDF| GeneratePDF[Generate PDF Report]
    ExportOptions -->|Excel| ExportExcel[Export to Excel/CSV]
    ExportOptions -->|None| End([Report Complete])

    PrintReport --> End
    GeneratePDF --> End
    ExportExcel --> End
```

## Error Handling in Sales Flow

```mermaid
flowchart TD
    Start([Sale Operation Started]) --> TryOperation[Try Database Operation]
    TryOperation --> Success{Operation Successful?}

    Success --> |Yes| LogSuccess[Log Success Event]
    LogSuccess --> CommitTransaction[Commit Transaction]
    CommitTransaction --> InvalidateCache[Invalidate Relevant Caches]
    InvalidateCache --> NotifySuccess[Notify User of Success]
    NotifySuccess --> End([Operation Complete])

    Success --> |No| CatchError[Catch Exception]
    CatchError --> ErrorType{Error Type}

    ErrorType -->|ValidationError| HandleValidation[Handle Validation Error]
    ErrorType -->|NotFoundError| HandleNotFound[Handle Not Found Error]
    ErrorType -->|BusinessRuleError| HandleBusinessRule[Handle Business Rule Error]
    ErrorType -->|DatabaseError| HandleDatabase[Handle Database Error]
    ErrorType -->|Other| LogUnknown[Log Unknown Error]

    HandleValidation --> UserValidation[Show User-Friendly Validation Message]
    HandleNotFound --> UserNotFound[Show "Record Not Found" Message]
    HandleBusinessRule --> UserBusinessRule[Show Business Rule Violation]
    HandleDatabase --> LogDatabaseError[Log Database Error with Stack Trace]
    LogUnknown --> LogUnknownError[Log Error with Full Context]

    UserValidation --> CheckTransaction{Transaction Active?}
    UserNotFound --> CheckTransaction
    UserBusinessRule --> CheckTransaction
    LogDatabaseError --> RollbackTransaction
    LogUnknownError --> RollbackTransaction

    CheckTransaction --> |Yes| RollbackTransaction[Rollback Transaction]
    CheckTransaction --> |No| EndError([End with Error])

    RollbackTransaction --> NotifyError[Notify User of Error]
    NotifyError --> LogAudit[Log Error in Audit Trail]
    LogAudit --> EndError
```

## Key Business Rules

### Sale Validation Rules

1. **Customer Requirements**
   - Customer must exist and be active
   - For credit sales: customer balance + sale total <= credit limit

2. **Product Requirements**
   - All products must exist and be active
   - Quantity must be positive
   - Quantity must not exceed available stock
   - Unit price must be positive (or zero for free items)

3. **Pricing Rules**
   - Default unit price = product.sale_price
   - Override allowed with proper authorization
   - Discount cannot exceed unit price
   - Line subtotal = (unit_price × quantity) - discount

4. **Payment Rules**
   - Cash: Payment amount must equal sale total
   - Credit: No payment required at time of sale
   - Debit/Transfer: Payment amount must equal sale total

5. **Tax Calculation**
   - Tax rate = TAX_RATE (default 10%)
   - Tax amount = subtotal × TAX_RATE
   - Total = subtotal + tax_amount

### Stock Management Rules

1. **Stock Deduction**
   - Stock deducted when sale is completed
   - Quantity deducted per sale item
   - Stock cannot go negative (validation prevents this)

2. **Stock Restoration**
   - Stock restored when sale is cancelled
   - Full quantity restored per sale item
   - Transactional: all or nothing

3. **Stock Adjustments**
   - Can increase or decrease stock
   - Requires reason for audit trail
   - Cannot result in negative stock

### Payment Rules

1. **Payment Validation**
   - Payment amount must be positive
   - Payment amount cannot exceed sale total (for cash/debit/transfer)
   - Payment amount cannot exceed remaining balance (for credit sales)

2. **Multiple Payments**
   - Multiple payments allowed for credit sales
   - Sum of payments cannot exceed sale total
   - Sale status changes to 'paid' when fully paid

3. **Payment Methods**
   - Cash: Immediate payment
   - Credit: Adds to customer balance
   - Debit: Electronic payment
   - Transfer: Bank transfer

---

**Document Version:** 1.0
**Last Updated:** 2025-03-14
