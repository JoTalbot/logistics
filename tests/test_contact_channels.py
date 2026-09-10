import pytest

from logistics.contact_channels import (
    ContactChannel,
    ContactChannelError,
    authorize_for_human_review,
    prepare_contact_intent,
)


def test_contact_intent_is_never_sendable_by_default():
    intent = prepare_contact_intent(
        channel=ContactChannel.EMAIL,
        target="sales@example.com",
        message="Request freight availability.",
        authorized=True,
    )
    assert intent.sendable is False
    approved = authorize_for_human_review(intent)
    assert approved.sendable is True


def test_unauthorized_contact_cannot_be_approved():
    intent = prepare_contact_intent(
        channel=ContactChannel.TELEGRAM,
        target="@customer",
        message="Hello",
        authorized=False,
    )
    with pytest.raises(ContactChannelError):
        authorize_for_human_review(intent)


def test_suppressed_contact_cannot_be_approved():
    intent = prepare_contact_intent(
        channel=ContactChannel.PHONE,
        target="+380000000000",
        message="Hello",
        authorized=True,
        suppressed=True,
    )
    assert intent.sendable is False
    with pytest.raises(ContactChannelError):
        authorize_for_human_review(intent)
