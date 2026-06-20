import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from app.core.config import settings

def send_otp_email(to_email: str, to_name: str, otp_code: str):
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = settings.BREVO_API_KEY

    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
        sib_api_v3_sdk.ApiClient(configuration)
    )

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
        to=[{"email": to_email, "name": to_name}],
        sender={"email": settings.FROM_EMAIL, "name": settings.FROM_NAME},
        subject="BloodBank — Your OTP Code",
        html_content=f"""
        <div style="font-family: Arial, sans-serif; max-width: 480px; margin: auto; padding: 32px; background: #fff; border-radius: 16px; border: 1px solid #eee;">
            <h1 style="color: #b91c1c; font-size: 24px; margin-bottom: 8px;">🩸 BloodBank</h1>
            <p style="color: #555; font-size: 15px;">Hi {to_name},</p>
            <p style="color: #555; font-size: 15px;">Your OTP code for password reset is:</p>
            <div style="background: #fef2f2; border: 2px dashed #b91c1c; border-radius: 12px; padding: 24px; text-align: center; margin: 24px 0;">
                <span style="font-size: 40px; font-weight: bold; letter-spacing: 12px; color: #b91c1c;">{otp_code}</span>
            </div>
            <p style="color: #888; font-size: 13px;">This OTP expires in <strong>10 minutes</strong>. Do not share it with anyone.</p>
            <p style="color: #888; font-size: 13px;">If you didn't request this, please ignore this email.</p>
            <hr style="border: none; border-top: 1px solid #eee; margin: 24px 0;">
            <p style="color: #bbb; font-size: 12px; text-align: center;">BloodBank — Saving Lives Together 🩸</p>
        </div>
        """
    )

    try:
        api_instance.send_transac_email(send_smtp_email)
        return True
    except ApiException as e:
        print(f"Brevo email error: {e}")
        return False