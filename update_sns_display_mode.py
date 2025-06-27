#!/usr/bin/env python3
"""
Update SNS blocks to use OGP card display mode
"""
from app import app
from models import db, ArticleBlock, BlockType

def update_sns_display_modes():
    """Update SNS blocks to use OGP card display mode"""
    with app.app_context():
        # Get SNS block type
        sns_block_type = BlockType.query.filter_by(type_name='sns_embed').first()
        if not sns_block_type:
            print("SNS embed block type not found!")
            return
        
        # Get all SNS blocks with OGP data
        sns_blocks = ArticleBlock.query.filter(
            ArticleBlock.block_type_id == sns_block_type.id,
            ArticleBlock.embed_url.isnot(None),
            ArticleBlock.ogp_title.isnot(None),
            ArticleBlock.ogp_title != ''
        ).all()
        
        print(f"Found {len(sns_blocks)} SNS blocks with OGP data")
        
        for block in sns_blocks:
            current_settings = block.get_settings_json()
            if current_settings.get('display_mode') != 'ogp_card':
                print(f"Updating block {block.id} to OGP card mode")
                current_settings['display_mode'] = 'ogp_card'
                block.set_settings_json(current_settings)
            else:
                print(f"Block {block.id} already in OGP card mode")
        
        db.session.commit()
        print("Display modes updated successfully!")

if __name__ == '__main__':
    update_sns_display_modes()