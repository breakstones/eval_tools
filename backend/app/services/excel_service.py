"""Service for Excel import/export operations."""

import io
from typing import Optional, List, Tuple
try:
    from typing import Self
except ImportError:
    from typing_extensions import Self

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case_set import CaseSet
from app.models.test_case import TestCase
from app.schemas.cases import CaseSetCreate, ExcelRowData, TestCaseCreate
from app.services.case_service import CaseService


class ExcelParseError(Exception):
    """Exception raised when Excel parsing fails."""

    def __init__(self, message: str, row: Optional[int] = None) -> None:
        """Initialize exception.

        Args:
            message: Error message
            row: Row number where error occurred (1-indexed)
        """
        self.message = message
        self.row = row
        super().__init__(f"Row {row}: {message}" if row else message)


class ExcelService:
    """Service for Excel import/export operations."""

    # Excel column mappings
    COL_CASE_UID = "用例编号"
    COL_DESCRIPTION = "用例描述"
    COL_USER_INPUT = "用户输入"
    COL_EXPECTED_OUTPUT = "预期输出"
    COL_SET_NAME = "用例集名称"
    COL_SYSTEM_PROMPT = "系统提示词"

    # Required columns for test cases
    REQUIRED_CASE_COLUMNS = {COL_USER_INPUT}

    def __init__(self, session: AsyncSession) -> None:
        """Initialize service with database session.

        Args:
            session: Database session
        """
        self.session = session
        self.case_service: Optional[CaseService] = None

    @classmethod
    async def create(cls, session: AsyncSession) -> Self:
        """Create a new service instance.

        Args:
            session: Database session

        Returns:
            ExcelService instance
        """
        service = cls(session)
        service.case_service = await CaseService.create(session)
        return service

    def _normalize_column_name(self, col: str) -> str:
        """Normalize column name for matching.

        Args:
            col: Column name to normalize

        Returns:
            Normalized column name
        """
        col = str(col).strip()
        mapping = {
            "用例编号": self.COL_CASE_UID,
            "编号": self.COL_CASE_UID,
            "id": self.COL_CASE_UID,
            "case_uid": self.COL_CASE_UID,
            "用例描述": self.COL_DESCRIPTION,
            "描述": self.COL_DESCRIPTION,
            "description": self.COL_DESCRIPTION,
            "用户输入": self.COL_USER_INPUT,
            "输入": self.COL_USER_INPUT,
            "user_input": self.COL_USER_INPUT,
            "预期输出": self.COL_EXPECTED_OUTPUT,
            "expected": self.COL_EXPECTED_OUTPUT,
            "expected_output": self.COL_EXPECTED_OUTPUT,
            "用例集名称": self.COL_SET_NAME,
            "用例集": self.COL_SET_NAME,
            "set_name": self.COL_SET_NAME,
            "系统提示词": self.COL_SYSTEM_PROMPT,
            "system_prompt": self.COL_SYSTEM_PROMPT,
        }
        return mapping.get(col.lower(), col)

    def _find_column_index(self, df: pd.DataFrame, target_col: str) -> Optional[int]:
        """Find the index of a column by normalized name.

        Args:
            df: DataFrame to search
            target_col: Target column name (normalized)

        Returns:
            Column index or None if not found
        """
        normalized_cols = [self._normalize_column_name(col) for col in df.columns]
        try:
            return normalized_cols.index(target_col)
        except ValueError:
            return None

    def _parse_case_set_info(self, df: pd.DataFrame) -> str:
        """Parse case set information from first row.

        Args:
            df: DataFrame containing Excel data

        Returns:
            Case set name

        Raises:
            ExcelParseError: If case set name is not found
        """
        first_row = df.iloc[0]

        # Try to find set name column
        set_name = None

        for col in df.columns:
            normalized = self._normalize_column_name(col)
            if normalized == self.COL_SET_NAME:
                set_name = str(first_row[col]).strip()

        # If no explicit columns, try to infer from first column
        if set_name is None or set_name == "" or set_name.lower() in ["nan", "none"]:
            first_col_value = str(first_row.iloc[0]).strip()
            if first_col_value and first_col_value.lower() not in ["nan", "none", "用例编号", "id"]:
                set_name = first_col_value

        if not set_name or set_name.lower() in ["nan", "none", ""]:
            raise ExcelParseError("用例集名称不能为空", row=1)

        return set_name

    def _parse_test_cases(self, df: pd.DataFrame, set_id: str) -> List[TestCaseCreate]:
        """Parse test cases from DataFrame.

        Args:
            df: DataFrame containing test case data
            set_id: Case set ID for the test cases

        Returns:
            List of parsed test cases

        Raises:
            ExcelParseError: If required columns are missing or data is invalid
        """
        # Find column indices
        user_input_idx = self._find_column_index(df, self.COL_USER_INPUT)
        case_uid_idx = self._find_column_index(df, self.COL_CASE_UID)
        description_idx = self._find_column_index(df, self.COL_DESCRIPTION)
        expected_idx = self._find_column_index(df, self.COL_EXPECTED_OUTPUT)

        if user_input_idx is None:
            raise ExcelParseError(f"缺少必需列: {self.COL_USER_INPUT}")

        test_cases = []
        for idx, row in df.iterrows():
            row_num = idx + 2  # 1-indexed, +1 for header row
            user_input = row.iloc[user_input_idx]

            # Skip empty rows
            if pd.isna(user_input) or str(user_input).strip() == "":
                continue

            # Extract case data
            case_uid = None
            if case_uid_idx is not None:
                case_uid_val = row.iloc[case_uid_idx]
                if pd.notna(case_uid_val) and str(case_uid_val).strip():
                    case_uid = str(case_uid_val).strip()

            description = None
            if description_idx is not None:
                desc_val = row.iloc[description_idx]
                if pd.notna(desc_val) and str(desc_val).strip():
                    description = str(desc_val).strip()

            expected_output = None
            if expected_idx is not None:
                expected_val = row.iloc[expected_idx]
                if pd.notna(expected_val) and str(expected_val).strip():
                    expected_output = str(expected_val).strip()

            test_cases.append(
                TestCaseCreate(
                    set_id=set_id,
                    case_uid=case_uid,
                    description=description,
                    user_input=str(user_input).strip(),
                    expected_output=expected_output,
                )
            )

        if not test_cases:
            raise ExcelParseError("未找到有效的测试用例数据")

        return test_cases

    async def import_excel(self, file_content: bytes, filename: str) -> Tuple[CaseSet, List[TestCase]]:
        """Import case set and test cases from Excel file.

        Args:
            file_content: Excel file content as bytes
            filename: Original filename

        Returns:
            Tuple of (created case set, created test cases)

        Raises:
            ExcelParseError: If Excel file is invalid
        """
        # Validate file extension
        if not filename.lower().endswith((".xlsx", ".xls")):
            raise ExcelParseError("仅支持 .xlsx 和 .xls 格式的文件")

        try:
            df = pd.read_excel(io.BytesIO(file_content))
        except Exception as e:
            raise ExcelParseError(f"无法读取Excel文件: {e!s}")

        if df.empty:
            raise ExcelParseError("Excel文件为空")

        # Parse case set info from first row
        set_name = self._parse_case_set_info(df)

        # Create case set
        case_set_data = CaseSetCreate(name=set_name)
        case_set = await self.case_service.create_case_set(case_set_data)

        # Parse test cases (skip first row which contains case set info)
        case_df = df.iloc[1:].reset_index(drop=True)
        test_cases_data = self._parse_test_cases(case_df, case_set.id)

        # Create test cases
        test_cases = await self.case_service.create_test_cases_batch(test_cases_data)

        return case_set, test_cases

    async def import_to_set(self, file_content: bytes, case_set: CaseSet) -> List[TestCase]:
        """Import test cases to an existing case set with deduplication by case_uid.

        Args:
            file_content: Excel file content as bytes
            case_set: Existing case set to import cases to

        Returns:
            List of created/updated test cases

        Raises:
            ExcelParseError: If Excel file is invalid
        """
        try:
            df = pd.read_excel(io.BytesIO(file_content))
        except Exception as e:
            raise ExcelParseError(f"无法读取Excel文件: {e!s}")

        if df.empty:
            raise ExcelParseError("Excel文件为空")

        # When importing to existing set, all rows are test cases
        # (First row with case set name was consumed as header by pandas)
        test_cases_data = self._parse_test_cases(df, case_set.id)

        # Use upsert to create or update test cases (deduplicate by case_uid)
        test_cases = await self.case_service.upsert_test_cases_batch(test_cases_data)

        return test_cases

    async def export_excel(self, case_set_id: str) -> bytes:
        """Export case set and test cases to Excel file.

        Args:
            case_set_id: Case set ID to export

        Returns:
            Excel file content as bytes

        Raises:
            ValueError: If case set not found
        """
        # Get case set
        case_set = await self.case_service.get_case_set(case_set_id)
        if case_set is None:
            raise ValueError(f"用例集不存在: {case_set_id}")

        # Get test cases
        test_cases = await self.case_service.get_test_cases(case_set_id)

        # Create DataFrame with test cases only (no case set info row)
        data = []
        for tc in test_cases:
            data.append(
                {
                    "用例编号": tc.case_uid or "",
                    "用例描述": tc.description or "",
                    "用户输入": tc.user_input,
                    "预期输出": tc.expected_output or "",
                }
            )

        df = pd.DataFrame(data)

        # Write to Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Sheet1")
        output.seek(0)

        return output.read()
