"""Tests for Excel parsing functionality."""

import io

import pandas as pd
import pytest

from app.services.excel_service import ExcelParseError, ExcelService
from app.schemas.cases import CaseSetCreate


class TestExcelService:
    """Tests for ExcelService."""

    @pytest.fixture
    async def excel_service(self, db_session):
        """Create Excel service for testing."""
        return await ExcelService.create(db_session)

    def test_normalize_column_name(self, excel_service):
        """Test column name normalization."""
        assert excel_service._normalize_column_name("用例编号") == "用例编号"
        assert excel_service._normalize_column_name("编号") == "用例编号"
        assert excel_service._normalize_column_name("id") == "用例编号"
        assert excel_service._normalize_column_name("用户输入") == "用户输入"
        assert excel_service._normalize_column_name("输入") == "用户输入"
        assert excel_service._normalize_column_name("预期输出") == "预期输出"
        assert excel_service._normalize_column_name("expected") == "预期输出"

    def test_find_column_index(self, excel_service):
        """Test finding column index by normalized name."""
        df = pd.DataFrame({
            "ID": ["1", "2"],
            "用户输入": ["input1", "input2"],
            "预期输出": ["output1", "output2"],
        })
        assert excel_service._find_column_index(df, "用例编号") == 0
        assert excel_service._find_column_index(df, "用户输入") == 1
        assert excel_service._find_column_index(df, "预期输出") == 2
        assert excel_service._find_column_index(df, "不存在") is None

    def test_parse_case_set_info_success(self, excel_service):
        """Test successful parsing of case set info."""
        df = pd.DataFrame({
            "用例集名称": ["测试集"],
            "系统提示词": ["You are a helpful assistant"],
        })
        name, prompt = excel_service._parse_case_set_info(df)
        assert name == "测试集"
        assert prompt == "You are a helpful assistant"

    def test_parse_case_set_info_missing_name(self, excel_service):
        """Test parsing case set info with missing name."""
        df = pd.DataFrame({
            "用户输入": [None],
        })
        with pytest.raises(ExcelParseError) as exc_info:
            excel_service._parse_case_set_info(df)
        assert "用例集名称不能为空" in str(exc_info.value)

    def test_parse_test_cases_success(self, excel_service):
        """Test successful parsing of test cases."""
        df = pd.DataFrame({
            "用例编号": ["CASE-001", "CASE-002"],
            "用例描述": ["测试1", "测试2"],
            "用户输入": ["input1", "input2"],
            "预期输出": ["output1", "output2"],
        })
        cases = excel_service._parse_test_cases(df, "test-set-id")
        assert len(cases) == 2
        assert cases[0].case_uid == "CASE-001"
        assert cases[0].description == "测试1"
        assert cases[0].user_input == "input1"
        assert cases[0].expected_output == "output1"

    def test_parse_test_cases_empty_user_input_skipped(self, excel_service):
        """Test that cases with empty user input are skipped."""
        df = pd.DataFrame({
            "用例编号": ["CASE-001", "CASE-002", "CASE-003"],
            "用户输入": ["input1", None, "input3"],
        })
        cases = excel_service._parse_test_cases(df, "test-set-id")
        assert len(cases) == 2
        assert cases[0].user_input == "input1"
        assert cases[1].user_input == "input3"

    def test_parse_test_cases_missing_required_column(self, excel_service):
        """Test parsing with missing required column."""
        df = pd.DataFrame({
            "用例编号": ["CASE-001"],
            "用例描述": ["测试1"],
        })
        with pytest.raises(ExcelParseError) as exc_info:
            excel_service._parse_test_cases(df, "test-set-id")
        assert "缺少必需列" in str(exc_info.value)

    def test_parse_test_cases_no_valid_data(self, excel_service):
        """Test parsing when no valid data is found."""
        df = pd.DataFrame({
            "用例编号": [None, None],
            "用户输入": [None, None],
        })
        with pytest.raises(ExcelParseError) as exc_info:
            excel_service._parse_test_cases(df, "test-set-id")
        assert "未找到有效的测试用例数据" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_import_excel_success(self, excel_service):
        """Test successful Excel import."""
        # Create Excel file content
        df = pd.DataFrame({
            "用例集名称": ["测试集", "", ""],
            "系统提示词": ["You are helpful", "", ""],
            "用例编号": ["", "CASE-001", "CASE-002"],
            "用例描述": ["", "测试1", "测试2"],
            "用户输入": ["测试集名称", "input1", "input2"],
            "预期输出": ["You are helpful", "output1", "output2"],
        })
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False)
        output.seek(0)
        content = output.read()

        case_set, cases = await excel_service.import_excel(content, "test.xlsx")
        assert case_set.name == "测试集"
        assert case_set.system_prompt == "You are helpful"
        assert len(cases) == 2
        assert cases[0].case_uid == "CASE-001"

    @pytest.mark.asyncio
    async def test_import_excel_invalid_extension(self, excel_service):
        """Test Excel import with invalid file extension."""
        with pytest.raises(ExcelParseError) as exc_info:
            await excel_service.import_excel(b"content", "test.txt")
        assert "仅支持" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_import_excel_empty_file(self, excel_service):
        """Test Excel import with empty file."""
        with pytest.raises(ExcelParseError) as exc_info:
            await excel_service.import_excel(b"", "test.xlsx")
        assert "无法读取" in str(exc_info.value) or "为空" in str(exc_info.value)
