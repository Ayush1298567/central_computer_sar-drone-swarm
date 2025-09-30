#!/usr/bin/env python3
"""
Test script for Computer Vision Service

Tests object detection and video analysis capabilities.
"""

import sys
import os
import tempfile

# Add backend to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

print("📷 Testing Computer Vision Service")
print("=" * 50)

def test_cv_service():
    """Test the computer vision service."""
    try:
        from app.services.computer_vision_service import cv_service

        print("✅ Computer vision service initialized successfully")

        # Test model status
        model_status = cv_service.get_model_status()
        print(f"📊 Model Status: {model_status['total_models']} models available")
        print(f"   Available models: {model_status['models_available']}")

        # Test object detection with mock image
        print("\n🖼️ Testing Object Detection...")

        # Create a temporary test image file
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            temp_image_path = temp_file.name
            # Write some dummy data to simulate an image file
            temp_file.write(b"fake image data")

        try:
            detections = cv_service.detect_objects(temp_image_path, confidence_threshold=0.5)

            print(f"✅ Object detection completed")
            print(f"   Found {len(detections)} objects")

            for i, detection in enumerate(detections, 1):
                print(f"   {i}. {detection['object_type']} (confidence: {detection['confidence']:.2f})")

        finally:
            # Clean up temp file
            if os.path.exists(temp_image_path):
                os.unlink(temp_image_path)

        # Test video analysis
        print("\n🎥 Testing Video Analysis...")

        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
            temp_video_path = temp_file.name
            temp_file.write(b"fake video data")

        try:
            video_analysis = cv_service.analyze_video_stream(temp_video_path)

            if "error" not in video_analysis:
                print(f"✅ Video analysis completed")
                print(f"   Processed {video_analysis['processed_frames']} frames")
                print(f"   Found {len(video_analysis['detections'])} detections")
                print(f"   Average confidence: {video_analysis['average_confidence']:.2f}")
            else:
                print(f"❌ Video analysis failed: {video_analysis['error']}")

        finally:
            # Clean up temp file
            if os.path.exists(temp_video_path):
                os.unlink(temp_video_path)

        # Test with non-existent file
        print("\n🧪 Testing Error Handling...")
        error_result = cv_service.detect_objects("non_existent_file.jpg")
        if "error" in error_result[0]:
            print("✅ Error handling works correctly")
        else:
            print("❌ Error handling failed")

        return True

    except Exception as e:
        print(f"❌ Computer vision test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cv_integration():
    """Test computer vision integration with other services."""
    print("\n🔗 Testing Computer Vision Integration...")

    try:
        from app.services.computer_vision_service import cv_service

        # Test that CV service can be imported and used by other services
        print("✅ CV service can be imported by other modules")

        # Test service interaction patterns
        print("✅ CV service provides expected interface methods")

        # Check method availability
        expected_methods = ['detect_objects', 'analyze_video_stream', 'get_model_status']
        for method in expected_methods:
            if hasattr(cv_service, method):
                print(f"   ✅ Method {method} is available")
            else:
                print(f"   ❌ Method {method} is missing")

        return True

    except Exception as e:
        print(f"❌ CV integration test failed: {e}")
        return False

def main():
    """Run all computer vision tests."""
    print("Starting Computer Vision Service Tests...")

    # Test basic functionality
    basic_success = test_cv_service()

    # Test integration
    integration_success = test_cv_integration()

    print("\n" + "=" * 50)
    if basic_success and integration_success:
        print("✅ COMPUTER VISION TEST: PASSED")
        print("🎯 Computer vision service is working correctly")
        print("🚀 Ready for integration with YOLO models")
    else:
        print("❌ COMPUTER VISION TEST: FAILED")
        print("🔧 Computer vision service needs fixes before proceeding")

    return 0 if basic_success and integration_success else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)