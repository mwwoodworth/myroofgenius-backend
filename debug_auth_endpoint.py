
# Add this to your auth routes for debugging
@router.post("/debug-login")
async def debug_login(user_credentials: UserLogin):
    """Debug login endpoint with detailed error handling"""
    try:
        print(f"🔍 Debug login attempt for: {user_credentials.email}")

        with db_engine.connect() as conn:
            # Get user from database
            result = conn.execute(
                text("""
                    SELECT id, email, hashed_password, is_active, is_verified,
                           failed_login_attempts, locked_until
                    FROM app_users
                    WHERE email = :email
                """),
                {"email": user_credentials.email}
            )
            user = result.fetchone()

            if not user:
                return {"error": "User not found", "step": "user_lookup"}

            print(f"✅ User found: {user.email}")

            # Check if account is active
            if not user.is_active:
                return {"error": "Account inactive", "step": "active_check"}

            print("✅ Account is active")

            # Test password verification
            try:
                password_valid = verify_password(user_credentials.password, user.hashed_password)
                print(f"✅ Password verification result: {password_valid}")

                if not password_valid:
                    return {"error": "Invalid password", "step": "password_verification"}

            except Exception as e:
                return {"error": f"Password verification failed: {str(e)}", "step": "password_verification"}

            # Test token creation
            try:
                access_token = create_access_token({"user_id": str(user.id)})
                print(f"✅ Token created: {access_token[:50]}...")

            except Exception as e:
                return {"error": f"Token creation failed: {str(e)}", "step": "token_creation"}

            # Test database update
            try:
                conn.execute(
                    text("""
                        UPDATE app_users
                        SET failed_login_attempts = 0, locked_until = NULL, last_login = :now
                        WHERE id = :user_id
                    """),
                    {
                        "now": datetime.utcnow(),
                        "user_id": user.id
                    }
                )
                conn.commit()
                print("✅ Database update successful")

            except Exception as e:
                return {"error": f"Database update failed: {str(e)}", "step": "database_update"}

            return {
                "success": True,
                "message": "Debug login successful",
                "user_id": str(user.id),
                "access_token": access_token
            }

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return {"error": f"Unexpected error: {str(e)}", "step": "unexpected"}
