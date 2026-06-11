"""
One-off script to restore bottle_barrel_picker associations lost during
the MySQL -> PostgreSQL migration.

Run with: flask shell < scripts/restore_bottle_barrel_picker.py
"""
from mywhiskies.extensions import db

rows = [
    ("10b9a90a-13a3-41be-a690-29994242e1cf", "0e40257c-f37c-4795-b9e0-abc6501d0cec"),
    ("cb007161-1605-4481-aca7-6d67a8df160a", "0e40257c-f37c-4795-b9e0-abc6501d0cec"),
    ("ff99939b-5c46-41c2-980c-cddb927bb720", "0e40257c-f37c-4795-b9e0-abc6501d0cec"),
    ("8a266edc-f445-4651-abc7-cadfbce1a04c", "205d909b-5c39-44bb-8261-b13598f1ebcc"),
    ("a835b201-5716-4d3e-82ad-a2a983bc2502", "22db7044-68e0-4cff-9647-ec69c683772b"),
    ("6f682c55-2cd9-4c75-807e-5193bc8ac98e", "24a55344-dc9b-402d-8537-80ba0eb94f57"),
    ("b55eb9b7-5b37-46de-a583-976d898bd1cc", "2a61a55b-d793-43fe-ba4a-7860f9e43d0b"),
    ("2b925e88-202d-4ec0-ae1a-5370119a8e1e", "3072c8f8-e332-4aaf-bf77-e502828821d2"),
    ("c9ed0eb2-2571-4c5d-8359-f3275678e9be", "3072c8f8-e332-4aaf-bf77-e502828821d2"),
    ("3ca6f499-b5d3-4da2-8290-a29efb2d2ae6", "318e29b8-a4cc-4171-942d-bdd8c0bbcaf2"),
    ("3e6abfcb-e4ce-4801-ab72-aaa8f374d746", "318e29b8-a4cc-4171-942d-bdd8c0bbcaf2"),
    ("c9ed0eb2-2571-4c5d-8359-f3275678e9be", "377a1798-c3f8-4414-86b5-3dfa317eeb81"),
    ("26ed006b-abad-41b2-b911-f48b3096e884", "3c03b46d-e8b0-420f-b686-9137cb68166b"),
    ("cc5d1e72-5238-4132-8514-bc2d28911ab6", "441ce390-1ad0-494a-b1ad-055ec49a2f66"),
    ("d37d4bd4-7815-4d95-8966-aaa8a8db42a1", "4b15642e-a4a0-405d-b6ca-3938527adc32"),
    ("dc5b44a7-cbcc-4d8f-bb81-4eda5836064b", "4b15642e-a4a0-405d-b6ca-3938527adc32"),
    ("3ef5d9bf-dfac-4507-87c5-78f96f0cc7ca", "525f75fa-6d58-47a7-802e-0ac32b7685f3"),
    ("8c05b2c5-0e11-47b0-879e-aa292ec173d2", "60a6acd7-a664-485e-99e9-11b865be2018"),
    ("22924ddd-1006-4ab8-a251-e461e188e43f", "624ff37c-c540-4128-8f88-b17a04bd844c"),
    ("69ab7a06-e4a9-4436-8a66-c468b348d524", "624ff37c-c540-4128-8f88-b17a04bd844c"),
    ("86951da4-7f97-49a4-8ac7-6bafcea893b9", "624ff37c-c540-4128-8f88-b17a04bd844c"),
    ("af58c475-8bf8-4908-8682-501c324ceb4a", "624ff37c-c540-4128-8f88-b17a04bd844c"),
    ("c59de164-7c13-4317-90dc-531ef6590bc4", "624ff37c-c540-4128-8f88-b17a04bd844c"),
    ("c9ed0eb2-2571-4c5d-8359-f3275678e9be", "67046e17-94d1-4ae7-8d09-c009e26e7b28"),
    ("28e96062-3f4f-487d-ba6a-11d72723ccef", "74384ba1-5729-49f3-b4fc-1c0b7bb92e04"),
    ("842532e3-9788-463e-90e2-fb613dff6bd5", "76e3b0e7-7f4d-4e31-b76a-0da9bdf8c876"),
    ("365d7642-56ff-4577-a7c2-6f08ef3fb449", "80c9b423-cef6-4479-a24d-1dd8f023683e"),
    ("91d167ba-8431-4cc5-b9a5-bc491c147052", "80c9b423-cef6-4479-a24d-1dd8f023683e"),
    ("b57b5b5a-d2e7-44a6-84fa-803a6386c461", "82746f89-5f5e-4fff-bcec-f9775d4f574b"),
    ("01714d02-49d7-4502-bd60-d9487c3f827a", "843c8f0a-ccb5-47dd-80e4-01e166724cb1"),
    ("0214968d-4c58-49cd-ac3d-16f5d5ef03cf", "843c8f0a-ccb5-47dd-80e4-01e166724cb1"),
    ("04645a91-9bd8-44f5-8e0d-5a1c17b7f69f", "843c8f0a-ccb5-47dd-80e4-01e166724cb1"),
    ("11f3a283-530e-4c9e-9a0b-8b5c137aa8a9", "843c8f0a-ccb5-47dd-80e4-01e166724cb1"),
    ("17e66c92-041e-4285-871c-6ed3e6803c83", "843c8f0a-ccb5-47dd-80e4-01e166724cb1"),
    ("25d13cf3-84bd-450f-b74a-a55f8ea4273f", "843c8f0a-ccb5-47dd-80e4-01e166724cb1"),
    ("354e0288-145d-49d9-8cf3-6039d1f8938d", "843c8f0a-ccb5-47dd-80e4-01e166724cb1"),
    ("3be44ff8-412c-49c9-8883-dcca41f972d6", "843c8f0a-ccb5-47dd-80e4-01e166724cb1"),
    ("a63d850c-fac2-4b26-9054-9eab01d87fc1", "843c8f0a-ccb5-47dd-80e4-01e166724cb1"),
    ("a9d6fc2a-51db-4b84-ab44-b4ed0fc6f968", "843c8f0a-ccb5-47dd-80e4-01e166724cb1"),
    ("cf19fc04-9c45-4724-ade8-31a9053dde3a", "843c8f0a-ccb5-47dd-80e4-01e166724cb1"),
    ("dc5b44a7-cbcc-4d8f-bb81-4eda5836064b", "843c8f0a-ccb5-47dd-80e4-01e166724cb1"),
    ("f77d7b69-1437-4d56-aa78-aaf64b2c44af", "843c8f0a-ccb5-47dd-80e4-01e166724cb1"),
    ("2b925e88-202d-4ec0-ae1a-5370119a8e1e", "91257b10-03d8-4708-935b-57c3d6fcda9b"),
    ("2b925e88-202d-4ec0-ae1a-5370119a8e1e", "91e442eb-f56d-4dc8-af12-17d3831df72c"),
    ("9d41efef-4a20-4c15-a472-4cd355d3d247", "91e442eb-f56d-4dc8-af12-17d3831df72c"),
    ("c0c6943f-90f0-4c6d-a903-5dc4f922bdbd", "91e442eb-f56d-4dc8-af12-17d3831df72c"),
    ("c9ed0eb2-2571-4c5d-8359-f3275678e9be", "91e442eb-f56d-4dc8-af12-17d3831df72c"),
    ("ceaec29c-75f0-41e0-9699-7b5df8f1caf3", "91e442eb-f56d-4dc8-af12-17d3831df72c"),
    ("eff95e7a-2817-4c07-8fc1-36eed065a59c", "91e442eb-f56d-4dc8-af12-17d3831df72c"),
    ("b55eb9b7-5b37-46de-a583-976d898bd1cc", "93c2c063-c8f4-434b-97ec-ba679cd8d1ee"),
    ("2b925e88-202d-4ec0-ae1a-5370119a8e1e", "97139f1d-3c03-4929-b701-8dad7582d81d"),
    ("c9ed0eb2-2571-4c5d-8359-f3275678e9be", "97139f1d-3c03-4929-b701-8dad7582d81d"),
    ("259a641f-384e-4000-9cea-c2ed64b6c91a", "b0785218-d401-410b-879b-523f2fcdbb69"),
    ("65f70647-a719-465d-9a69-6fe8ce7691f9", "b0785218-d401-410b-879b-523f2fcdbb69"),
    ("ceaec29c-75f0-41e0-9699-7b5df8f1caf3", "b0785218-d401-410b-879b-523f2fcdbb69"),
    ("04615d5e-07b3-4031-b8ab-47cea9c5f05b", "b1e7acad-3783-4c8c-a43c-3f3fff045b3b"),
    ("0f769834-2ee5-4a93-9f06-be16ca1a381c", "bc83655d-7e56-437b-9232-3c06765ac518"),
    ("16bc29a6-f7d1-4c0f-ae73-512862e4b9ae", "bc83655d-7e56-437b-9232-3c06765ac518"),
    ("2a276b6c-81b3-4f51-b785-b1f62a292097", "bc83655d-7e56-437b-9232-3c06765ac518"),
    ("34f4a718-be38-48c1-946f-0468d912ef5b", "bc83655d-7e56-437b-9232-3c06765ac518"),
    ("661dc562-32e1-417a-9427-f548255ed39b", "bc83655d-7e56-437b-9232-3c06765ac518"),
    ("abbd4299-56f5-4ba8-9695-391169e22ecd", "bc83655d-7e56-437b-9232-3c06765ac518"),
    ("cd385119-d6d7-4e51-acf5-4ee308464f4a", "bc83655d-7e56-437b-9232-3c06765ac518"),
    ("16322c36-0a52-4ad7-930d-7ee25484f21e", "c1582991-f03b-42ce-8934-43f5a80752e4"),
    ("64696f03-dadc-408e-af49-f00ecc325740", "d98c56e2-55e7-471a-a46a-d739e88b80b1"),
    ("1b29c547-930f-4dd2-a8c3-fb71cf3197ab", "dba4b281-be0b-49f6-954c-8e0d3a56d800"),
    ("05b1d301-bbe1-4537-a4ab-9b067ed7f15b", "df3257b5-5acf-4d6c-a449-01875620646e"),
    ("067f078c-c6fa-4777-b2e3-f27589ce1df9", "df8a5ab6-7d87-4efe-a5db-17d25f46ff43"),
    ("0e52a65c-bd87-4910-80a0-05dc1fe93f9f", "df8a5ab6-7d87-4efe-a5db-17d25f46ff43"),
    ("118aea1f-0d79-4b1b-b9a0-504f4dd12545", "df8a5ab6-7d87-4efe-a5db-17d25f46ff43"),
    ("33dcea60-84b6-4dd7-890e-cb9ba3f59d6a", "df8a5ab6-7d87-4efe-a5db-17d25f46ff43"),
    ("3ee40c24-05b3-4f9f-878f-1b3ee47ed6e8", "df8a5ab6-7d87-4efe-a5db-17d25f46ff43"),
    ("74850ac6-6304-4daf-83be-b5d95ed5fa9e", "df8a5ab6-7d87-4efe-a5db-17d25f46ff43"),
    ("59ef3975-acfd-45ee-a80d-3fc9d8bde927", "e09cf121-9df3-4259-8e04-e7cca270eadb"),
    ("4764de2d-d84f-4da9-83e6-d3b063506736", "e693a110-a43c-4a32-8ae0-bdfed31063f0"),
    ("6a4930a5-a84a-443b-aa7e-b81a3a3f4ba2", "e693a110-a43c-4a32-8ae0-bdfed31063f0"),
    ("ef5cfa46-77ff-4f52-aa5e-4c921959679e", "e693a110-a43c-4a32-8ae0-bdfed31063f0"),
    ("31bac554-1dbd-4cc5-a6ed-b21b3f6f8cb3", "ea0dc33f-cea1-4e34-82b2-b8b299322aa6"),
    ("c9ed0eb2-2571-4c5d-8359-f3275678e9be", "f105e240-9bb8-4979-b750-f730030ae71c"),
    ("22924ddd-1006-4ab8-a251-e461e188e43f", "fd83c2c4-b9e3-4ac6-a572-38a175e25e55"),
    ("58958fc1-d1f8-4dda-8295-5fbc21fd8201", "fd83c2c4-b9e3-4ac6-a572-38a175e25e55"),
    ("86951da4-7f97-49a4-8ac7-6bafcea893b9", "fd83c2c4-b9e3-4ac6-a572-38a175e25e55"),
    ("a835b201-5716-4d3e-82ad-a2a983bc2502", "fd83c2c4-b9e3-4ac6-a572-38a175e25e55"),
    ("af58c475-8bf8-4908-8682-501c324ceb4a", "fd83c2c4-b9e3-4ac6-a572-38a175e25e55"),
    ("c59de164-7c13-4317-90dc-531ef6590bc4", "fd83c2c4-b9e3-4ac6-a572-38a175e25e55"),
    ("2b925e88-202d-4ec0-ae1a-5370119a8e1e", "fe0bcd32-81e2-4af6-9b4d-a24ddcc920f7"),
    ("6eb44c96-5ac1-4955-8240-1061dad06277", "fe0bcd32-81e2-4af6-9b4d-a24ddcc920f7"),
    ("c9ed0eb2-2571-4c5d-8359-f3275678e9be", "fe0bcd32-81e2-4af6-9b4d-a24ddcc920f7"),
]

inserted = 0
skipped = 0

with db.engine.connect() as conn:
    for bottle_id, barrel_picker_id in rows:
        result = conn.execute(
            db.text(
                "INSERT INTO bottle_barrel_picker (bottle_id, barrel_picker_id) "
                "VALUES (:bid, :pid) ON CONFLICT DO NOTHING"
            ),
            {"bid": bottle_id, "pid": barrel_picker_id},
        )
        if result.rowcount:
            inserted += 1
        else:
            skipped += 1
    conn.commit()

print(f"Done: {inserted} inserted, {skipped} skipped (already existed).")
