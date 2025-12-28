# Multi-Unit Sales Fix - Implementation Guide

## Problem Identified

**DVF data contains multi-unit sales as separate rows**, causing:
- Duplicate counting of same transaction
- Incorrect price/m² calculations
- Misleading comparable sales

### Example
Address: 56 RUE NOTRE-DAME DES CHAMPS, 75006
Date: 07/12/2021

**Current (WRONG)**:
```
Sale 1: 54 m² for 1,340,000€ = 24,815€/m² ❌
Sale 2: 97.37 m² for 1,340,000€ = 13,762€/m² ❌
```

**Should be (CORRECT)**:
```
ONE Sale: 151.37 m² (54 + 97.37) for 1,340,000€ = 8,852€/m² ✅
  ├─ Lot 1: 97.37 m² apartment (2 rooms)
  └─ Lot 3: 54 m² apartment (2 rooms)
```

---

## Solution Implemented

### 1. ✅ Database View Created

Created materialized view `dvf_grouped_transactions` that:
- Groups records by `transaction_group_id`
- Aggregates surface areas and room counts
- Calculates correct grouped price/m²
- Stores lot details for drill-down

**File**: `backend/alembic/versions/create_grouped_transactions_view.sql`

**Key fields**:
- `total_surface_area`: SUM of all lots
- `total_rooms`: SUM of all lots
- `unit_count`: Number of lots in transaction
- `grouped_price_per_sqm`: price / total_surface_area
- `lots_detail`: JSON array of individual lots

---

## TODO: Implementation Steps

### 2. Create SQLAlchemy Model

**File**: `backend/app/models/property.py`

Add this class:

```python
class DVFGroupedTransaction(Base):
    """Materialized view of grouped DVF transactions (multi-unit sales aggregated)."""

    __tablename__ = "dvf_grouped_transactions"

    id = Column(Integer, primary_key=True)
    transaction_group_id = Column(String(32), unique=True, index=True)

    # Transaction info
    sale_date = Column(Date, index=True)
    sale_price = Column(Float)

    # Address
    address = Column(String)
    postal_code = Column(String, index=True)
    city = Column(String)
    department = Column(String)
    property_type = Column(String, index=True)

    # Aggregated metrics
    total_surface_area = Column(Float)
    total_land_surface = Column(Float)
    total_rooms = Column(Integer)
    unit_count = Column(Integer)  # Number of lots/units
    grouped_price_per_sqm = Column(Float)

    # Metadata
    data_year = Column(Integer)
    source_file = Column(String)
    import_batch_id = Column(String(36))
    created_at = Column(DateTime)

    # Lot details for drill-down (JSON)
    lots_detail = Column(Text)  # JSON array
```

### 3. Update DVF Service

**File**: `backend/app/services/dvf_service.py`

Add new methods:

```python
from app.models.property import DVFGroupedTransaction

@staticmethod
def get_grouped_exact_address_sales(
    db: Session,
    postal_code: str,
    property_type: str,
    address: str,
    months_back: int = 60,
    max_results: int = 20
) -> List[DVFGroupedTransaction]:
    """
    Get GROUPED sales (multi-unit sales aggregated) for exact address.
    Returns ONE row per transaction, not per lot.
    """
    cutoff_date = datetime.now() - timedelta(days=30 * months_back)
    street_number, street_name = DVFService.extract_street_info(address)

    if not street_number or not street_name:
        return []

    query = db.query(DVFGroupedTransaction).filter(
        DVFGroupedTransaction.sale_date >= cutoff_date,
        DVFGroupedTransaction.property_type == property_type,
        DVFGroupedTransaction.total_surface_area.isnot(None),
        DVFGroupedTransaction.grouped_price_per_sqm.isnot(None),
        DVFGroupedTransaction.grouped_price_per_sqm > 0,
        DVFGroupedTransaction.postal_code == postal_code,
        DVFGroupedTransaction.address.ilike(f'{street_number} {street_name}%')
    ).order_by(DVFGroupedTransaction.sale_date.desc()).limit(max_results)

    return query.all()
```

### 4. Update API Endpoints

**File**: `backend/app/api/properties.py` (or routes/properties.py)

Modify the simple_price_analysis endpoint to:

1. Call `get_grouped_exact_address_sales()` instead of `get_exact_address_sales()`
2. Return additional fields in response:
   - `unit_count`: Number of lots
   - `is_multi_unit`: Boolean flag
   - `lots_detail`: Array for drill-down

Example response structure:

```python
{
    "exact_address_sales": [
        {
            "sale_date": "2021-12-07",
            "sale_price": 1340000,
            "surface_area": 151.37,  # TOTAL
            "rooms": 4,  # TOTAL
            "price_per_sqm": 8852.48,  # CORRECT
            "address": "56 RUE NOTRE-DAME DES CHAMPS",
            "postal_code": "75006",
            "unit_count": 2,  # NEW
            "is_multi_unit": true,  # NEW
            "lots_detail": [  # NEW - for drill-down
                {
                    "surface_area": 97.37,
                    "rooms": 2,
                    "price_per_sqm": 13761.94
                },
                {
                    "surface_area": 54,
                    "rooms": 2,
                    "price_per_sqm": 24814.81
                }
            ]
        }
    ]
}
```

### 5. Update Frontend

**File**: `frontend/src/pages/PropertyDetails.tsx` (or similar)

Add drill-down UI for multi-unit sales:

```tsx
{sale.is_multi_unit && sale.unit_count > 1 && (
  <Accordion>
    <AccordionSummary>
      <Typography>
        Multi-unit sale ({sale.unit_count} lots) - Click to see details
      </Typography>
    </AccordionSummary>
    <AccordionDetails>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>Lot</TableCell>
            <TableCell>Surface</TableCell>
            <TableCell>Rooms</TableCell>
            <TableCell>Individual €/m²</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {sale.lots_detail.map((lot, idx) => (
            <TableRow key={idx}>
              <TableCell>Lot {idx + 1}</TableCell>
              <TableCell>{lot.surface_area} m²</TableCell>
              <TableCell>{lot.rooms}</TableCell>
              <TableCell>{lot.price_per_sqm.toFixed(0)} €/m²</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </AccordionDetails>
  </Accordion>
)}
```

---

## Testing

### Validate with Known Example

```sql
-- Should return ONE row with correct aggregated data
SELECT
    sale_date,
    sale_price,
    total_surface_area,
    unit_count,
    ROUND(grouped_price_per_sqm::numeric, 2) as price_sqm,
    lots_detail
FROM dvf_grouped_transactions
WHERE address = '56 RUE NOTRE-DAME DES CHAMPS'
  AND postal_code = '75006'
  AND sale_date = '2021-12-07';

-- Expected result:
-- sale_date: 2021-12-07
-- sale_price: 1,340,000
-- total_surface_area: 151.37
-- unit_count: 2
-- price_sqm: 8,852.48
```

---

## Data Refresh

The materialized view needs to be refreshed after new imports:

```sql
-- Manual refresh
REFRESH MATERIALIZED VIEW CONCURRENTLY dvf_grouped_transactions;

-- Or use the function
SELECT refresh_dvf_grouped_transactions();
```

**Add this to import scripts** at the end:
```bash
echo "Refreshing grouped transactions view..."
docker exec appartment-agent-db-1 psql -U appartment -d appartment_agent -c "
SELECT refresh_dvf_grouped_transactions();
"
```

---

## Benefits

✅ **Accurate price/m²**: Calculated on total transaction, not individual lots
✅ **No duplicate counting**: One transaction = one record
✅ **Transparent**: Can drill down to see individual lots
✅ **Better analysis**: Trend and comparison calculations are correct

---

## Files Modified

1. ✅ `backend/alembic/versions/create_grouped_transactions_view.sql` - View creation
2. ⏳ `backend/app/models/property.py` - Add DVFGroupedTransaction model
3. ⏳ `backend/app/services/dvf_service.py` - Add grouped query methods
4. ⏳ `backend/app/api/properties.py` - Update simple_price_analysis endpoint
5. ⏳ `frontend/src/pages/PropertyDetails.tsx` - Add drill-down UI
6. ⏳ `backend/scripts/fast_import_dvf_final.sh` - Add view refresh step

---

## Status

- [x] Database view created and tested
- [ ] SQLAlchemy model added
- [ ] Service methods updated
- [ ] API endpoints updated
- [ ] Frontend drill-down UI implemented
- [ ] Import scripts updated to refresh view
- [ ] End-to-end testing completed

**Next Action**: Implement steps 2-6 above to complete the fix.
