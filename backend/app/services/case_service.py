"""Service for case set and test case management."""

from collections.abc import AsyncIterator
from typing import Optional, List
try:
    from typing import Self
except ImportError:
    from typing_extensions import Self

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case_set import CaseSet
from app.models.test_case import TestCase
from app.schemas.cases import CaseSetCreate, CaseSetUpdate, TestCaseCreate, TestCaseUpdate


class CaseService:
    """Service for managing case sets and test cases."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize service with database session.

        Args:
            session: Database session
        """
        self.session = session

    @classmethod
    async def create(cls, session: AsyncSession) -> Self:
        """Create a new service instance.

        Args:
            session: Database session

        Returns:
            CaseService instance
        """
        return cls(session)

    async def get_case_sets(self) -> List[CaseSet]:
        """Get all case sets.

        Returns:
            List of case sets
        """
        result = await self.session.execute(select(CaseSet).order_by(CaseSet.created_at.desc()))
        return list(result.scalars().all())

    async def get_case_set(self, case_set_id: str) -> Optional[CaseSet]:
        """Get a case set by ID.

        Args:
            case_set_id: Case set ID

        Returns:
            Case set or None if not found
        """
        result = await self.session.execute(select(CaseSet).where(CaseSet.id == case_set_id))
        return result.scalar_one_or_none()

    async def create_case_set(self, data: CaseSetCreate) -> CaseSet:
        """Create a new case set.

        Args:
            data: Case set creation data

        Returns:
            Created case set
        """
        case_set = CaseSet(
            name=data.name,
        )
        self.session.add(case_set)
        await self.session.flush()
        await self.session.refresh(case_set)
        return case_set

    async def update_case_set(self, case_set_id: str, data: CaseSetUpdate) -> Optional[CaseSet]:
        """Update a case set.

        Args:
            case_set_id: Case set ID
            data: Update data

        Returns:
            Updated case set or None if not found
        """
        case_set = await self.get_case_set(case_set_id)
        if case_set is None:
            return None

        if data.name is not None:
            case_set.name = data.name

        await self.session.flush()
        await self.session.refresh(case_set)
        return case_set

    async def delete_case_set(self, case_set_id: str) -> bool:
        """Delete a case set and all its test cases.

        Args:
            case_set_id: Case set ID

        Returns:
            True if deleted, False if not found
        """
        case_set = await self.get_case_set(case_set_id)
        if case_set is None:
            return False

        # Delete associated test cases
        await self.session.execute(delete(TestCase).where(TestCase.set_id == case_set_id))

        # Delete case set
        await self.session.execute(delete(CaseSet).where(CaseSet.id == case_set_id))
        return True

    async def get_test_cases(self, set_id: str) -> List[TestCase]:
        """Get all test cases for a case set.

        Args:
            set_id: Case set ID

        Returns:
            List of test cases
        """
        result = await self.session.execute(
            select(TestCase)
            .where(TestCase.set_id == set_id)
            .order_by(TestCase.created_at.asc())
        )
        return list(result.scalars().all())

    async def get_test_case(self, case_id: str) -> Optional[TestCase]:
        """Get a test case by ID.

        Args:
            case_id: Test case ID

        Returns:
            Test case or None if not found
        """
        result = await self.session.execute(select(TestCase).where(TestCase.id == case_id))
        return result.scalar_one_or_none()

    async def create_test_case(self, data: TestCaseCreate) -> TestCase:
        """Create a new test case.

        Args:
            data: Test case creation data

        Returns:
            Created test case
        """
        test_case = TestCase(
            set_id=data.set_id,
            case_uid=data.case_uid,
            description=data.description,
            user_input=data.user_input,
            expected_output=data.expected_output,
        )
        self.session.add(test_case)
        await self.session.flush()
        await self.session.refresh(test_case)
        return test_case

    async def create_test_cases_batch(self, cases_data: List[TestCaseCreate]) -> List[TestCase]:
        """Create multiple test cases in batch.

        Args:
            cases_data: List of test case creation data

        Returns:
            List of created test cases
        """
        test_cases = [
            TestCase(
                set_id=data.set_id,
                case_uid=data.case_uid,
                description=data.description,
                user_input=data.user_input,
                expected_output=data.expected_output,
            )
            for data in cases_data
        ]
        self.session.add_all(test_cases)
        await self.session.flush()
        for tc in test_cases:
            await self.session.refresh(tc)
        return test_cases

    async def update_test_case(self, case_id: str, data: TestCaseUpdate) -> Optional[TestCase]:
        """Update a test case.

        Args:
            case_id: Test case ID
            data: Update data

        Returns:
            Updated test case or None if not found
        """
        test_case = await self.get_test_case(case_id)
        if test_case is None:
            return None

        if data.case_uid is not None:
            test_case.case_uid = data.case_uid
        if data.description is not None:
            test_case.description = data.description
        if data.user_input is not None:
            test_case.user_input = data.user_input
        if data.expected_output is not None:
            test_case.expected_output = data.expected_output

        await self.session.flush()
        await self.session.refresh(test_case)
        return test_case

    async def delete_test_case(self, case_id: str) -> bool:
        """Delete a test case.

        Args:
            case_id: Test case ID

        Returns:
            True if deleted, False if not found
        """
        test_case = await self.get_test_case(case_id)
        if test_case is None:
            return False

        await self.session.execute(delete(TestCase).where(TestCase.id == case_id))
        return True

    async def get_case_count(self, set_id: str) -> int:
        """Get the count of test cases in a case set.

        Args:
            set_id: Case set ID

        Returns:
            Count of test cases
        """
        result = await self.session.execute(
            select(func.count(TestCase.id)).where(TestCase.set_id == set_id)
        )
        return result.scalar() or 0

    async def get_test_case_by_uid(self, set_id: str, case_uid: str) -> Optional[TestCase]:
        """Get a test case by case_uid within a case set.

        Args:
            set_id: Case set ID
            case_uid: Test case UID

        Returns:
            Test case or None if not found
        """
        result = await self.session.execute(
            select(TestCase)
            .where(TestCase.set_id == set_id)
            .where(TestCase.case_uid == case_uid)
        )
        return result.scalar_one_or_none()

    async def upsert_test_cases_batch(self, cases_data: List[TestCaseCreate]) -> List[TestCase]:
        """Create or update multiple test cases in batch.

        For each case, if a case with the same case_uid exists in the set, it will be updated.
        Otherwise, a new case will be created.

        Args:
            cases_data: List of test case creation data

        Returns:
            List of created/updated test cases
        """
        result_cases = []
        for data in cases_data:
            # Check if a case with the same case_uid exists
            existing_case = None
            if data.case_uid:
                existing_case = await self.get_test_case_by_uid(data.set_id, data.case_uid)

            if existing_case:
                # Update existing case
                if data.description is not None:
                    existing_case.description = data.description
                if data.user_input is not None:
                    existing_case.user_input = data.user_input
                if data.expected_output is not None:
                    existing_case.expected_output = data.expected_output
                await self.session.flush()
                await self.session.refresh(existing_case)
                result_cases.append(existing_case)
            else:
                # Create new case
                new_case = TestCase(
                    set_id=data.set_id,
                    case_uid=data.case_uid,
                    description=data.description,
                    user_input=data.user_input,
                    expected_output=data.expected_output,
                )
                self.session.add(new_case)
                await self.session.flush()
                await self.session.refresh(new_case)
                result_cases.append(new_case)

        return result_cases

    async def duplicate_case_set(self, case_set_id: str, new_name: str) -> Optional[CaseSet]:
        """Duplicate a case set and all its test cases.

        Args:
            case_set_id: Source case set ID
            new_name: Name for the duplicated case set

        Returns:
            Created case set with duplicated test cases, or None if source not found
        """
        # Get source case set
        source_set = await self.get_case_set(case_set_id)
        if source_set is None:
            return None

        # Get source test cases
        source_cases = await self.get_test_cases(case_set_id)

        # Create new case set
        new_set = CaseSet(name=new_name)
        self.session.add(new_set)
        await self.session.flush()
        await self.session.refresh(new_set)

        # Duplicate all test cases
        for source_case in source_cases:
            new_case = TestCase(
                set_id=new_set.id,
                case_uid=source_case.case_uid,
                description=source_case.description,
                user_input=source_case.user_input,
                expected_output=source_case.expected_output,
            )
            self.session.add(new_case)

        await self.session.flush()
        await self.session.refresh(new_set)

        return new_set
